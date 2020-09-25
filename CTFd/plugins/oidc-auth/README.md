# CTFd OIDC Authentication Plugin

Add OIDC authentication to CTFd 2.x using compatible providers. Users can be linked between the CTFd User database and the OAuth provider; these users can be created on the fly or not. Based on CTFd-OAuth2 plugin by...

**This plugin is still in development and may not work properly in your configuration.**

✅ `Authlib` and `Loginpass` are required.

## Supported Providers:
* `azure`
* `github` (GitHub)
* ... and any other Loginpass provider, with a little work!

## Configuration
The following configuration options must be defined in `config.py`:
```
OIDC_CLIENT_ID - OIDC Provider Client ID
OIDC_CLIENT_SECRET - OIDC Provider Client Secret
OAUTHLOGIN_PROVIDER - OIDC Provider name (see 'Supported Providers' above)
OIDC_CREATE_MISSING_USER - If the plugin should create a CTFd user to link to the OAuth2 user
```

## Extensibility:
Extensibility beyoud Azure still need a little work.
