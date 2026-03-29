#!/bin/bash
# Shared SSH/SCP connection options and host allowlist check for all ssh_*.sh tools.
# Source this file, then use: ssh "${SSH_OPTS[@]}" or scp "${SCP_OPTS[@]}"
#
# Optional env var: SSH_PORT — set by the skill when host uses a non-default port.
# ssh uses -p (lowercase), scp uses -P (uppercase), so two arrays are needed.
_BASE_OPTS=(
  -o BatchMode=yes                          # Disable password prompts; fail fast if key auth is missing
  -o ConnectTimeout=10                      # Abort if the host doesn't respond within 10 seconds
  -o StrictHostKeyChecking=accept-new       # Auto-accept new host keys; reject changed keys (TOFU)
  -o ControlMaster=auto                     # First connection creates a master socket; subsequent ones reuse it
  -o ControlPath=/tmp/ssh_mux_%r@%h:%p     # Socket path — %r=user, %h=host, %p=port (one socket per machine)
  -o ControlPersist=60                      # Keep the master socket alive 60s after the last connection closes
)
# check_allowed_host USER@IP — call after sourcing ssh_config.sh
# Extracts the IP/hostname and checks it against ALLOWED_HOSTS.
check_allowed_host() {
  local host="${1#*@}"   # strip user@ prefix
  [[ "$DISABLE_HOST_RESTRICTION" == "true" ]] && return 0
  for entry in "${ALLOWED_HOSTS[@]}"; do
    [[ "${entry#*=}" == "$host" ]] && return 0
  done
  echo "BLOCKED: '$host' is not in ALLOWED_HOSTS — add it to ssh_config.sh" >&2
  return 1
}

if [[ -n "$SSH_PORT" ]]; then
  SSH_OPTS=("${_BASE_OPTS[@]}" -p "$SSH_PORT")
  SCP_OPTS=("${_BASE_OPTS[@]}" -P "$SSH_PORT")
else
  SSH_OPTS=("${_BASE_OPTS[@]}")
  SCP_OPTS=("${_BASE_OPTS[@]}")
fi
