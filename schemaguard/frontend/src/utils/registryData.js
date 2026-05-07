import { registryAPI } from '../api/client';

export async function fetchRegistriesWithVersions() {
  const data = await registryAPI.list();
  return Promise.all(
    (data.registries || []).map(async (registry) => {
      try {
        const fullRegistry = await registryAPI.get(registry.id);
        return { ...registry, versions: fullRegistry.versions || [] };
      } catch {
        return { ...registry, versions: [] };
      }
    })
  );
}

export function flattenDiffs(registries) {
  return registries.flatMap((registry) =>
    (registry.versions || [])
      .filter((version) => version.diff_result)
      .map((version) => ({ registry, version, diff: version.diff_result }))
  );
}
