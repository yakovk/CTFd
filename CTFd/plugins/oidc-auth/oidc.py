import os

from flask import render_template, session, redirect, jsonify, url_for
from authlib.integrations.flask_client import OAuth
from loginpass import create_flask_blueprint

from CTFd.auth import confirm, register, reset_password, login
from CTFd.models import db, Users
from CTFd.utils import set_config
from CTFd.utils.logging import log
from CTFd.utils.security.auth import login_user, logout_user

from CTFd import utils

SUPPORTED_BACKENDS = ['azure']

def load(app):
    url_prefix = "/oidc"
    oidc_login_backend = app.config.setdefault('OIDC_LOGIN_BACKEND',
                                               os.environ.get('OIDC_LOGIN_BACKEND', None))
    create_missing_user = app.config.setdefault('OIDC_CREATE_MISSING_USER',
                                                os.environ.get('OIDC_CREATE_MISSING_USER', False))

    def get_user(email):
        user = Users.query.filter_by(email=email).first()
        if user is not None:
            log('logins', "[{date}] {ip} - " +
                email + " - OIDC bridged user found")
            return user

    def create_user(email, name):
        log('logins', "[{date}] {ip} - " + email +
            " - No OIDC bridged user found, creating user")
        user = Users(email=email, name=name.strip(), verified=True)
        db.session.add(user)
        db.session.commit()
        return user
    
    def get_or_create_user(email, name):
        user = get_user(email)
        if user is not None:
            return user
        if create_missing_user:
            return create_user(email, name)
        else:
            log('logins', "[{date}] {ip} - " + email +
                " - No OIDC bridged user found and not configured to create missing users")
            return None

    def handle_authorize(remote, token, user_info):

        with app.app_context():
            user = get_or_create_user(
                email=user_info["email"],
                name=user_info["name"])

            if user is not None:
                session.regenerate()
                login_user(user)
                log("logins", "[{date}] {ip} - " + user.name + " logged in")
                db.session.close()
                return redirect(url_for("challenges.listing"))

        return redirect('/')


    def create_azure_backend(name, tenant='common'):

        metadata_url = f'https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration'

        class AzureAD(object):
            NAME = name
            OAUTH_CONFIG = {
                'api_base_url': 'https://graph.microsoft.com/',
                'server_metadata_url': metadata_url,
                'client_kwargs': {'scope': 'openid email profile'},
            }

            def load_server_metadata(self):
                metadata = super(AzureAD, self).load_server_metadata()
                # fix issuer value
                issuer = metadata['issuer']
                issuer = issuer.replace('{tenantid}', tenant)
                metadata['issuer'] = issuer
                return metadata

        return AzureAD

    backend = None

    if oidc_login_backend == 'azure':
        app.config.setdefault('AZURE_TENANT_ID',
                              os.environ.get('AZURE_TENANT_ID', 'common'))
        app.config.setdefault('AZURE_CLIENT_ID',
                              os.environ.get('AZURE_CLIENT_ID', 'missing_client_id'))
        app.config.setdefault('AZURE_CLIENT_SECRET',
                              os.environ.get('AZURE_CLIENT_SECRET', 'missing_client_secret'))
        backend = create_azure_backend('azure', app.config['AZURE_TENANT_ID'])
    else:
        print('** Skip loading CTFd-OIDC because of the unknown or unsupported OIDC backend **')
        return

    oauth = OAuth(app)

    bp = create_flask_blueprint([backend], oauth, handle_authorize)
    app.register_blueprint(bp, url_prefix=url_prefix)

    ###############################
    # Application Reconfiguration #
    ###############################
    # ('', 204) is "No Content" code
    set_config('registration_visibility', False)
    app.view_functions['auth.login'] = lambda: redirect(
        url_prefix + "/login/" + oidc_login_backend)
    app.view_functions['auth.register'] = lambda: ('', 204)
    app.view_functions['auth.reset_password'] = lambda: ('', 204)
    app.view_functions['auth.confirm'] = lambda: ('', 204)     
