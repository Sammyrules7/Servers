#!/bin/bash
set -euo pipefail
token=''
api() {
  local auth=()
  [[ -z "$token" ]] || auth=(-H "Authorization: Bearer $token")
  curl --silent --show-error --fail-with-body --connect-timeout 5 --max-time 15 \
    --connect-to satisfactory.maio-tech.com:7777:satisfactory.satisfactory.svc:7777 \
    -H 'Content-Type: application/json' "${auth[@]}" \
    --data "$1" https://satisfactory.maio-tech.com:7777/api/v1 |
    jq -e 'if (.errorCode // "") != "" then error(.errorCode) else . end'
}
until api '{"function":"HealthCheck","data":{"ClientCustomData":""}}' >/dev/null 2>&1; do
  sleep 10
done
login=$(api '{"function":"PasswordlessLogin","data":{"MinimumPrivilegeLevel":"InitialAdmin"}}' || true)
token=$(jq -r '.data.authenticationToken // .data.AuthenticationToken // empty' <<< "$login")
if [[ -n "$token" ]]; then
  response=$(api "$(jq -nc --arg password "$ADMIN_PASSWORD" \
    '{function:"ClaimServer",data:{ServerName:"Maio Factory",AdminPassword:$password}}')")
  token=$(jq -er '.data.authenticationToken // .data.AuthenticationToken' <<< "$response")
  echo 'Server claimed.'
else
  response=$(api "$(jq -nc --arg password "$ADMIN_PASSWORD" \
    '{function:"PasswordLogin",data:{MinimumPrivilegeLevel:"Administrator",Password:$password}}')")
  token=$(jq -er '.data.authenticationToken // .data.AuthenticationToken' <<< "$response")
fi
api "$(jq -nc --arg password "$PLAYER_PASSWORD" \
  '{function:"SetClientPassword",data:{Password:$password}}')" >/dev/null
api '{"function":"ApplyServerOptions","data":{"UpdatedServerOptions":{"FG.DSAutoPause":"True","FG.DSAutoSaveOnDisconnect":"True"}}}' >/dev/null
echo 'Player password set; auto-pause and save on disconnect enabled.'
