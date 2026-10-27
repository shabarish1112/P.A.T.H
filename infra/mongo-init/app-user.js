const database = db.getSiblingDB('path');
const collections = ['transactions', 'anomalies', 'reviews', 'refresh_tokens', 'users',
  'datasets', 'model_runs', 'jobs', 'settings', 'login_attempts', 'locks'];
if (!database.getCollectionNames().includes('audit_logs')) {
  database.createCollection('audit_logs', { validator: { $jsonSchema: {
    bsonType: 'object',
    required: ['actor_id', 'actor_email', 'action', 'resource_type', 'created_at', 'expire_at'],
    properties: { created_at: { bsonType: 'date' }, expire_at: { bsonType: 'date' } },
  } } });
}
database.audit_logs.createIndex({ created_at: -1 });
database.audit_logs.createIndex({ expire_at: 1 }, { expireAfterSeconds: 0 });
const privileges = collections.map(collection => ({
  resource: { db: 'path', collection },
  actions: ['find', 'insert', 'update', 'remove', 'createIndex', 'listIndexes', 'createCollection', 'collMod'],
}));
privileges.push({ resource: { db: 'path', collection: '' }, actions: ['listCollections'] });
privileges.push({ resource: { db: 'path', collection: 'audit_logs' },
  actions: ['find', 'insert', 'listIndexes'] });
if (database.getRole('pathApplication')) {
  database.updateRole('pathApplication', { privileges, roles: [] });
} else {
  database.createRole({ role: 'pathApplication', privileges, roles: [] });
}
if (database.getUser(process.env.PATH_APP_USER)) {
  database.updateUser(process.env.PATH_APP_USER, { roles: [{ role: 'pathApplication', db: 'path' }] });
} else {
  database.createUser({ user: process.env.PATH_APP_USER, pwd: process.env.PATH_APP_PASSWORD,
    roles: [{ role: 'pathApplication', db: 'path' }] });
}
