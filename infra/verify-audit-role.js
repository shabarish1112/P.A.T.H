const database = db.getSiblingDB('path');
if (!database.auth(process.env.PATH_APP_USER, process.env.PATH_APP_PASSWORD)) {
  throw new Error('Application authentication failed');
}
database.audit_logs.insertOne({ actor_id: 'permission-check', actor_email: '',
  action: 'permission.verify', resource_type: 'test', created_at: new Date(),
  expire_at: new Date(Date.now() + 86400000) });
database.audit_logs.findOne({ actor_id: 'permission-check' });
for (const command of [
  { update: 'audit_logs', updates: [{ q: {}, u: { $set: { action: 'forbidden' } } }] },
  { delete: 'audit_logs', deletes: [{ q: {}, limit: 0 }] },
  { drop: 'audit_logs' },
]) {
  const result = database.runCommand(command);
  if (result.ok || result.code !== 13) throw new Error('Audit mutation was not denied');
}
print('Audit find allowed; update, delete and drop denied.');
