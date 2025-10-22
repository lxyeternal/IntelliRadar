#!/bin/bash

# Set MongoDB host (default to localhost if not set)
MONGO_HOST=${MONGO_HOST:-localhost}

# Wait for MongoDB to start
echo "Waiting for MongoDB to start at ${MONGO_HOST}..."
until mongosh --host ${MONGO_HOST} --eval "print(\"MongoDB connection successful\")" > /dev/null 2>&1; do
    sleep 1
done

echo "MongoDB started, initializing database..."

# Restore intelliradar database from the backup data
if [ -d "/backup/database/intelliradar" ]; then
    echo "Restoring intelliradar database from backup..."
    mongorestore --host ${MONGO_HOST} --db intelliradar /backup/database/intelliradar/
    echo "intelliradar database restoration completed"
else
    echo "intelliradar backup data not found at /backup/database/intelliradar, skipping restoration"
fi

# Create user management database and collections
echo "Initializing user management database..."
mongosh --host ${MONGO_HOST} --eval "
use intelliradar_users;
db.createCollection('users');
db.createCollection('sessions');
db.users.createIndex({username: 1}, {unique: true});
db.users.createIndex({email: 1}, {unique: true});
db.sessions.createIndex({token: 1}, {unique: true});
db.sessions.createIndex({expires_at: 1}, {expireAfterSeconds: 0});
print('User management database initialization completed');
"

# Create indexes for intelliradar database
echo "Creating indexes for threat intelligence database..."
mongosh --host ${MONGO_HOST} --eval "
use intelliradar;
db.threat_intelligence.createIndex({package_name: 1});
db.threat_intelligence.createIndex({package_manager: 1});
db.threat_intelligence.createIndex({'metadata.confidence_level': 1});
db.threat_intelligence.createIndex({'metadata.created_at': -1});
db.threat_intelligence.createIndex({'metadata.last_updated': -1});
db.threat_intelligence.createIndex({id: 1}, {unique: true});
db.analysis.createIndex({package_name: 1});
db.analysis.createIndex({source: 1});
db.content.createIndex({source: 1});
db.content.createIndex({timestamp: -1});
db.links.createIndex({source: 1});
db.links.createIndex({collected_at: -1});
print('Threat intelligence database indexes creation completed');
"

echo "Database initialization completed!"
