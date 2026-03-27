#!/bin/bash

set -e

echo "Starting config server..."
mongod --configsvr \
       --replSet configReplSet \
       --port 27019 \
       --dbpath /data/configdb \
       --bind_ip_all \
       --fork \
       --logpath /data/configdb/config.log

sleep 5

echo "Initiating config replica set..."
mongosh --port 27019 <<EOF
rs.initiate({
  _id: "configReplSet",
  configsvr: true,
  members: [{ _id: 0, host: "localhost:27019" }]
})
EOF

sleep 5

echo "Starting shard server..."
mongod --shardsvr \
       --replSet shard1ReplSet \
       --port 27018 \
       --dbpath /data/shard1 \
       --bind_ip_all \
       --fork \
       --logpath /data/shard1/shard.log

sleep 5

echo "Initiating shard replica set..."
mongosh --port 27018 <<EOF
rs.initiate({
  _id: "shard1ReplSet",
  members: [{ _id: 0, host: "localhost:27018" }]
})
EOF

sleep 5

echo "Starting mongos..."
mongos --configdb configReplSet/localhost:27019 \
       --bind_ip_all \
       --port 27017 \
       --fork \
       --logpath /data/mongos.log

sleep 5

echo "Adding shard to cluster..."
mongosh --port 27017 <<EOF
sh.addShard("shard1ReplSet/localhost:27018")
EOF

echo "Creating admin user..."
mongosh --port 27017 <<EOF
use admin
db.createUser({
  user: "root_user",
  pwd: "root_pass",
  roles: [ { role: "root", db: "admin" } ]
})
EOF

echo "Cluster started successfully."

# Keep container running
tail -f /data/mongos.log
