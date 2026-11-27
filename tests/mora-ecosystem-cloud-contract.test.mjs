import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const contract = JSON.parse(
  await readFile(new URL('../federation/ecosystem-cloud.v1.json', import.meta.url), 'utf8'),
);

test('ecosystem cloud contract keeps local-only as the default', () => {
  assert.equal(contract.schema, 'ivan-vhs.ecosystem-cloud.v1');
  assert.equal(contract.version, 1);
  assert.equal(contract.architecture, 'local-first-cloud-optional');
  assert.equal(contract.default_mode, 'local-only');
  assert.equal(contract.network.default, 'disabled');
  assert.equal(contract.network.enablement, 'explicit-user-opt-in');
  assert.equal(contract.network.offline_fallback, 'required');
});

test('all five repositories have one unique, bounded adapter declaration', () => {
  const ids = contract.repositories.map((repository) => repository.id);
  assert.deepEqual([...ids].sort(), ['dakos', 'oplague', 'pytyliki', 'reaper', 'ventusample']);
  assert.equal(new Set(ids).size, 5);
  for (const repository of contract.repositories) {
    assert.equal(repository.project_key, repository.id);
    assert.equal(repository.adapter, 'federation/ecosystem-cloud-adapter.v1.json');
    assert.ok(repository.eligible.length > 0);
    assert.ok(repository.forbidden.length > 0);
  }
});

test('private storage and sync receipts never hold raw payloads', () => {
  assert.equal(contract.storage.visibility, 'private');
  assert.equal(contract.storage.public_urls, false);
  assert.equal(contract.storage.max_object_size_bytes, 104857600);
  assert.equal(contract.synchronization.payload_storage, 'domain-specific-only');
  assert.equal(contract.synchronization.client_instance_id, 'random UUID; never hardware-derived');
  assert.ok(contract.forbidden_data_classes.includes('service_role_keys'));
  assert.ok(contract.forbidden_data_classes.includes('raw_device_serial_numbers'));
  assert.ok(contract.forbidden_data_classes.includes('driver_binaries'));
});

test('DAKOS owns a local-only adapter and never syncs privileged state', async () => {
  const adapter = JSON.parse(
    await readFile(new URL('../federation/ecosystem-cloud-adapter.v1.json', import.meta.url), 'utf8'),
  );
  assert.equal(adapter.schema, 'ivan-vhs.ecosystem-cloud-adapter.v1');
  assert.equal(adapter.project, 'dakos');
  assert.equal(adapter.shared_contract, contract.schema);
  assert.equal(adapter.status, 'contract-only');
  assert.equal(adapter.runtime.default_network_mode, 'disabled');
  assert.equal(adapter.runtime.boot_requires_network, false);
  assert.equal(adapter.runtime.shell_requires_network, false);
  assert.ok(adapter.denylist.includes('boot-secrets'));
  assert.ok(adapter.denylist.includes('kernel-memory'));
  assert.ok(adapter.denylist.includes('service-role-keys'));
});

test('ecosystem cloud JSON Schema is closed and versioned', async () => {
  const schema = JSON.parse(
    await readFile(new URL('../schemas/ivan-vhs.ecosystem-cloud.v1.schema.json', import.meta.url), 'utf8'),
  );
  assert.equal(schema.$schema, 'https://json-schema.org/draft/2020-12/schema');
  assert.equal(schema.$id, 'https://github.com/Ivan-VHS/DAKOS/blob/main/schemas/ivan-vhs.ecosystem-cloud.v1.schema.json');
  assert.equal(schema.additionalProperties, false);
  assert.ok(schema.required.includes('repositories'));
  assert.equal(schema.properties.version.const, 1);
});
