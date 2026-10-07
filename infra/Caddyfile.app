{
    email {$ACME_EMAIL}
}
{$SITE_DOMAIN} {
    header Strict-Transport-Security "max-age=31536000"
    reverse_proxy nginx:80 {
        # Replace any client-supplied value. Nginx trusts this private hop.
        header_up X-Real-IP {remote_host}
    }
}
