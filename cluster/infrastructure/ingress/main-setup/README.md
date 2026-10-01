# The auth secret `auth-secret` is not created automatically for `basic-auth`  
# Create the secret with (replacing yourpassword)  
 `kubectl create secret generic auth-secret \
  -n ingress \
  --from-literal=users="sammy:$(nix-shell -p whois --run "mkpasswd -m bcrypt 'yourpassword'")"`


### This should be managed by sops

Let’s Encrypt certificates across namespaces use the shared
`lets-encrypt-issuer` ClusterIssuer, defined in
`../lets-encrypt-clusterissuer.yaml`. Its Cloudflare DNS token is SOPS encrypted
in `../cert-manager/cloudflare-dns-token.enc.yaml`; the token and ACME account
key live in the `cert-manager` namespace. Each Certificate keeps its TLS Secret
in its own namespace and references `issuerRef.kind: ClusterIssuer`.
