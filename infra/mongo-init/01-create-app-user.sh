#!/bin/sh
set -eu
mongosh --host localhost --authenticationDatabase admin -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" <<EOF
use path
db.createUser({
  user: "$PATH_APP_USER",
  pwd: "$PATH_APP_PASSWORD",
  roles: [{ role: "readWrite", db: "path" }]
})
EOF
