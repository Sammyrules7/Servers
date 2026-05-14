# The auth secret `auth-secret` is not created automatically for `basic-auth`  
# Create the secret with (replacing yourpassword)  
 `kubectl create secret generic auth-secret \
  -n ingress \
  --from-literal=users="sammy:$(nix-shell -p whois --run "mkpasswd -m bcrypt 'yourpassword'")"`
