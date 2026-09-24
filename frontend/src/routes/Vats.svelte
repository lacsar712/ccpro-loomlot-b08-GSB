<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS } from '../lib/api.js';
  import { user } from '../lib/auth.js';

  let houses = [];
  let rows = [];
  let error = '';
  let filterHouse = '';
  let form = {
    dyeHouseId: '',
    vatCode: '',
    fiberType: '棉',
    capacityL: 500,
    status: 'ready',
  };
  let editing = null;
  let reassignTarget = null;
  let reassignForm = { dyeHouseId: '', vatCode: '' };
  let reassignError = '';

  function vatsUrl() {
    return filterHouse ? `/vats?dyeHouseId=${filterHouse}` : '/vats';
  }

  async function load() {
    error = '';
    try {
      [houses, rows] = await Promise.all([api('/dye-houses'), api(vatsUrl())]);
      if (!form.dyeHouseId && houses.length) form.dyeHouseId = String(houses[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function houseName(id) {
    return houses.find((h) => h.id === id)?.name || id;
  }

  function isAdmin() {
    return $user?.role === 'admin';
  }

  async function save() {
    error = '';
    try {
      const body = {
        dyeHouseId: Number(form.dyeHouseId),
        vatCode: form.vatCode.trim(),
        fiberType: form.fiberType.trim(),
        capacityL: Number(form.capacityL),
        status: form.status,
      };
      if (editing) {
        await api(`/vats/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/vats', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      form = {
        dyeHouseId: form.dyeHouseId,
        vatCode: '',
        fiberType: '棉',
        capacityL: 500,
        status: 'ready',
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    reassignTarget = null;
    form = {
      dyeHouseId: String(row.dyeHouseId),
      vatCode: row.vatCode,
      fiberType: row.fiberType,
      capacityL: row.capacityL,
      status: row.status,
    };
  }

  function startReassign(row) {
    reassignTarget = row;
    editing = null;
    const other = houses.find((h) => h.id !== row.dyeHouseId);
    reassignForm = {
      dyeHouseId: other ? String(other.id) : String(row.dyeHouseId),
      vatCode: '',
    };
    reassignError = '';
  }

  function cancelReassign() {
    reassignTarget = null;
    reassignError = '';
  }

  async function submitReassign() {
    reassignError = '';
    try {
      const body = { dyeHouseId: Number(reassignForm.dyeHouseId) };
      const code = reassignForm.vatCode.trim();
      if (code) body.vatCode = code;
      await api(`/vats/${reassignTarget.id}/reassign`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      reassignTarget = null;
      await load();
    } catch (e) {
      reassignError = e.message;
    }
  }

  async function drain(id) {
    error = '';
    try {
      await api(`/vats/${id}/drain`, { method: 'POST' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function remove(id) {
    if (!confirm('确认删除该染缸？')) return;
    error = '';
    try {
      await api(`/vats/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">染缸</h1>
<p class="page-sub">状态：就绪 / 染色中 / 排液。容量单位为升。染缸跨坊调动请使用主管的「改挂」动作。</p>

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >所属染坊
      <select bind:value={form.dyeHouseId} disabled={!!editing}>
        {#each houses as h}
          <option value={String(h.id)}>{h.name}</option>
        {/each}
      </select>
    </label>
    <label>缸号 <input bind:value={form.vatCode} /></label>
    <label>纤维类型 <input bind:value={form.fiberType} /></label>
    <label>容量 (L) <input type="number" step="0.1" bind:value={form.capacityL} /></label>
    <label
      >状态
      <select bind:value={form.status}>
        <option value="ready">就绪</option>
        <option value="dyeing">染色中</option>
        <option value="drain">排液</option>
      </select>
    </label>
  </div>
  {#if editing}
    <p style="margin:0.5rem 0 0;color:var(--indigo-mist);font-size:0.85rem;">
      编辑模式下所属染坊不可直接更改，跨坊请使用行内「改挂」。
    </p>
  {/if}
  <div class="toolbar">
    <button class="btn" type="button" on:click={save}>{editing ? '保存修改' : '新建染缸'}</button>
    {#if editing}
      <button
        class="btn ghost"
        type="button"
        on:click={() => {
          editing = null;
        }}>取消</button
      >
    {/if}
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

{#if reassignTarget}
  <div class="panel" style="margin-bottom:1rem;border-left:3px solid var(--indigo-accent, #5b6cff);">
    <strong
      >改挂染缸 #{reassignTarget.id}（{houseName(reassignTarget.dyeHouseId)} ·
      {reassignTarget.vatCode}）</strong
    >
    {#if reassignTarget.status === 'dyeing'}
      <p class="err">该染缸尚有进行中的染程，请先「完成排液」后再改挂。</p>
    {/if}
    <div class="form-grid">
      <label
        >目标染坊
        <select bind:value={reassignForm.dyeHouseId}>
          {#each houses as h}
            <option value={String(h.id)}>{h.name}</option>
          {/each}
        </select>
      </label>
      <label
        >新缸号（可选）
        <input
          bind:value={reassignForm.vatCode}
          placeholder="留空沿用原号 {reassignTarget.vatCode}" />
      </label>
    </div>
    <div class="toolbar">
      <button class="btn" type="button" on:click={submitReassign}>确认改挂</button>
      <button class="btn ghost" type="button" on:click={cancelReassign}>取消</button>
    </div>
    {#if reassignError}<p class="err">{reassignError}</p>{/if}
  </div>
{/if}

<div class="panel">
  <div class="toolbar" style="margin-bottom:0.75rem;">
    <label style="margin:0;display:flex;align-items:center;gap:0.5rem;">
      <span>按染坊筛选</span>
      <select bind:value={filterHouse} on:change={load}>
        <option value="">全部染坊</option>
        {#each houses as h}
          <option value={h.id}>{h.name}</option>
        {/each}
      </select>
    </label>
  </div>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染坊</th>
        <th>缸号</th>
        <th>纤维</th>
        <th>容量 L</th>
        <th>状态</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{houseName(row.dyeHouseId)}</td>
          <td>{row.vatCode}</td>
          <td>{row.fiberType}</td>
          <td>{row.capacityL}</td>
          <td><span class="badge {row.status}">{VAT_STATUS[row.status] || row.status}</span></td>
          <td class="row-actions">
            {#if row.status !== 'drain'}
              <button class="btn ghost small" type="button" on:click={() => drain(row.id)}>完成排液</button>
            {/if}
            {#if isAdmin()}
              <button class="btn ghost small" type="button" on:click={() => startReassign(row)}>改挂</button>
            {/if}
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
