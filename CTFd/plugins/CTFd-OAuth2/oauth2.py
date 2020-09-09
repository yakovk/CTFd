from flask import render_template, session, redirect
from flask_dance.contrib import azure, github
import flask_dance.contrib

from CTFd.auth import confirm, register, reset_password, login
from CTFd.models import db, Users
from CTFd.utils import set_config
from CTFd.utils.logging import log
from CTFd.utils.security.auth import login_user, logout_user

from CTFd import utils

def load(app):
    ########################
    # Plugin Configuration #
    ########################
    authentication_url_prefix = "/auth"
    oauth_client_id = utils.get_app_config('OAUTHLOGIN_CLIENT_ID')
    oauth_client_secret = utils.get_app_config('OAUTHLOGIN_CLIENT_SECRET')
    oauth_provider = utils.get_app_config('OAUTHLOGIN_PROVIDER')
    create_missing_user = utils.get_app_config('OAUTHLOGIN_CREATE_MISSING_USER')

    ##################
    # User Functions #
    ##################
    def retrieve_user_from_database(username):
        user = Users.query.filter_by(email=username).first()
        if user is not None:
            log('logins', "[{date}] {ip} - " + username + " - OAuth2 bridged user found")
            return user
    def create_user(username, displayName):
        with app.app_context():
            log('logins', "[{date}] {ip} - " + username + " - No OAuth2 bridged user found, creating user")
            user = Users(email=username, name=displayName.strip(), verified=True)
            db.session.add(user)
            db.session.commit()
            return user
    def create_or_get_user(username, displayName):
        user = retrieve_user_from_database(username)
        if user is not None:
            return user
        if create_missing_user:
            return create_user(username, displayName)
        else:
            log('logins', "[{date}] {ip} - " + username + " - No OAuth2 bridged user found and not configured to create missing users")
            return None

    ##########################
    # Provider Configuration #
    ##########################
    provider_blueprints = {
        'azure': lambda: flask_dance.contrib.azure.make_azure_blueprint(
            login_url='/azure',
            client_id=oauth_client_id,
            client_secret=oauth_client_secret,
            redirect_url=authentication_url_prefix + "/azure/confirm"),
        'github': lambda: flask_dance.contrib.github.make_github_blueprint(
            login_url='/github',
            client_id=oauth_client_id,
            client_secret=oauth_client_secret,
            redirect_url=authentication_url_prefix + "/github/confirm")
    }

    def get_azure_user():
        resp = flask_dance.contrib.azure.azure.get("/v1.0/me")
        print(" * Azure.Get(/v1.0/me): %s" % resp.text)
        user_info = resp.json()
        return create_or_get_user(
            username=user_info["userPrincipalName"],
            displayName=user_info["displayName"])
    def get_github_user():
        user_info = flask_dance.contrib.github.github.get("/user").json()
        return create_or_get_user(
            username=user_info["email"],
            displayName=user_info["name"])

    provider_users = {
        'azure': lambda: get_azure_user(),
        'github': lambda: get_github_user()
    }

    if oauth_provider not in provider_blueprints:
        print('** Skip loading CTFd-OAuth2 because of the unknown or unsupported OAuth provider **')
        return

    provider_blueprint = provider_blueprints[oauth_provider]() # Resolved lambda
    
    #######################
    # Blueprint Functions #
    #######################
    @provider_blueprint.route('/<string:auth_provider>/confirm', methods=['GET'])
    def confirm_auth_provider(auth_provider):
        if auth_provider not in provider_users:
            return redirect('/')

        provider_user = provider_users[oauth_provider]() # Resolved lambda
        if provider_user is not None:
            session.regenerate()
            login_user(provider_user)
            db.session.close()   
        return redirect('/')

    app.register_blueprint(provider_blueprint, url_prefix=authentication_url_prefix)

    ###############################
    # Application Reconfiguration #
    ###############################
    # ('', 204) is "No Content" code
    set_config('registration_visibility', False)
    app.view_functions['auth.login'] = lambda: redirect(authentication_url_prefix + "/" + oauth_provider)
    app.view_functions['auth.register'] = lambda: ('', 204)
    app.view_functions['auth.reset_password'] = lambda: ('', 204)
    app.view_functions['auth.confirm'] = lambda: ('', 204)     
