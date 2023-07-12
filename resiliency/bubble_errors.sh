#!/usr/bin/env bash

cat <<EOF> /tmp/bubble_policy.tmp
policy_rule {
  name: "bubble_errors"
  description: ""
  enabled: true
  scope {
    global: true
  }
  policies {
    rpc_retry_operations {
      mode: RETRY_INTERACTIVE
    }
  }
}
EOF
qmgt policy-rule import /tmp/bubble_policy.tmp


