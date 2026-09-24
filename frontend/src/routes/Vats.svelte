<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS } from '../lib/api.js';
  import { user } from '../lib/auth.js';

  let houses = [];
  let rows = [];
  let error = '';
  let filterHouseId = '';
  let form = {
    dyeHouseId: '',
    vatCode: '',
    fiberType: '棉',
    capacityL: 500,
    status: 'ready',
  };
  let editing = null;
  let transferring = null;
  let transferForm = { targetDyeHouseId: '', newVatCode: '' };

  $: isAdmin = $user && $user.role === 'admin';

  async function load() {
    error = '';
    try {
      const vatPath = filterHouseId ? `/vats?dyeHouseId=${filterHouseId}` : '/vats';
      [houses, rows] = await Promise.all([api('/dye-houses'), api(vatPath)]);
      if (!form.dyeHouseId && houses.length) form.dyeHouseId = String(houses[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function houseName(id) {
    return houses.find((h) => h.id === id)?.name || id;
  }

  async function save() {
    error = '';
    try {
      if (editing) {
        // 染坊归属不在普通编辑内修改，须由主管走「改挂」
        const body = {
          vatCode: form.vatCode.trim(),
          fiberType: form.fiberType.trim(),
          capacityL: Number(form.capacityL),
          status: form.status,
        };
        await api(`/vats/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        const body = {
          dyeHouseId: Number(form.dyeHouseId),
          vatCode: form.vatCode.trim(),
          fiberType: form.fiberType.trim(),
          capacityL: Number(form.capacityL),
          status: form.status,
        };
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
    transferring = null;
    editing = row.id;
    form = {
      dyeHouseId: String(row.dyeHouseId),
      vatCode: row.vatCode,
      fiberType: row.fiberType,
      capacityL: row.capacityL,
      status: row.status,
    };
  }

  function startTransfer(row) {
    editing = null;
    error = '';
    transferring = row.id;
    const other = houses.find((h) => h.id !== row.dyeHouseId);
    transferForm = {
      targetDyeHouseId: other ? String(other.id) : '',
      newVatCode: '',
    };
  }

  async function doTransfer() {
    error = '';
    try {
      const body = { targetDyeHouseId: Number(transferForm.targetDyeHouseId) };
      const code = transferForm.newVatCode.trim();
      if (code) body.newVatCode = code;
      await api(`/vats/${transferring}/transfer`, { method: 'POST', body: JSON.stringify(body) });
      transferring = null;
      transferForm = { targetDyeHouseId: '', newVatCode: '' };
      await load();
    } catch (e) {
      error = e.message;
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
<p class="page-sub">
  状态：就绪 / 染色中 / 排液。容量单位为升。跨坊改挂仅染坊主管可操作，且染缸须无进行中染程（必要时先完成排液）。
</p>

{#if transferring}
  <div class="panel" style="margin-bottom:1rem;">
    <p style="margin:0 0 0.75rem;font-weight:600;">
      改挂染缸 #{transferring}：指定目标染坊，可另起新缸号（留空则沿用原号）。
    </p>
    <div class="form-grid">
      <label
        >目标染坊
        <select bind:value={transferForm.targetDyeHouseId}>
          {#each houses as h}
            <option value={String(h.id)}>{h.name}</option>
          {/each}
        </select>
      </label>
      <label>新缸号（可选） <input bind:value={transferForm.newVatCode} placeholder="留空沿用原缸号" /></label>
    </div>
    <div class="toolbar">
      <button class="btn" type="button" on:click={doTransfer}>确认改挂</button>
      <button class="btn ghost" type="button" on:click={() => (transferring = null)}>取消</button>
    </div>
    {#if error}<p class="err">{error}</p>{/if}
  </div>
{:else}
  <div class="panel" style="margin-bottom:1rem;">
    <div class="form-grid">
      {#if !editing}
        <label
          >所属染坊
          <select bind:value={form.dyeHouseId}>
            {#each houses as h}
              <option value={String(h.id)}>{h.name}</option>
            {/each}
          </select>
        </label>
      {/if}
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
{/if}

<div class="panel">
  <div class="toolbar" style="margin-bottom:0.75rem;">
    <label style="display:flex;align-items:center;gap:0.5rem;margin:0;">
      按染坊筛选
      <select bind:value={filterHouseId} on:change={load}>
        <option value="">全部染坊</option>
        {#each houses as h}
          <option value={String(h.id)}>{h.name}</option>
        {/each}
      </select>
    </label>
    <span style="color:var(--indigo-mist);font-size:0.85rem;">当前 {rows.length} 缸</span>
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
            {#if isAdmin}
              <button class="btn ghost small" type="button" on:click={() => startTransfer(row)}>改挂</button>
            {/if}
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
