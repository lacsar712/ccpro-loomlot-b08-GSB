<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS, toLocalInput, fromLocalInput } from '../lib/api.js';

  let houses = [];
  let vats = [];
  let rows = [];
  let error = '';
  let filterHouse = '';
  let form = {
    vatId: '',
    recipeName: '',
    fabricKg: 20,
    startedAt: toLocalInput(new Date().toISOString()),
    operatorName: '染程操作员',
  };
  let editing = null;

  async function load() {
    error = '';
    try {
      const qs = filterHouse ? `?dyeHouseId=${filterHouse}` : '';
      [vats, rows] = await Promise.all([api(`/vats${qs}`), api(`/dye-lots${qs}`)]);
      const usable = vats.filter((v) => v.status === 'ready' || v.status === 'dyeing');
      if (!form.vatId && usable.length) form.vatId = String(usable[0].id);
      else if (!form.vatId && vats.length) form.vatId = String(vats[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  async function loadHouses() {
    try {
      houses = await api('/dye-houses');
    } catch (e) {
      error = e.message;
    }
  }

  onMount(() => {
    loadHouses();
    load();
  });

  function vatLabel(id) {
    const v = vats.find((x) => x.id === id);
    if (!v) return id;
    return `${v.vatCode}（${VAT_STATUS[v.status] || v.status}）`;
  }

  async function save() {
    error = '';
    try {
      const body = {
        vatId: Number(form.vatId),
        recipeName: form.recipeName.trim(),
        fabricKg: Number(form.fabricKg),
        startedAt: fromLocalInput(form.startedAt),
        operatorName: form.operatorName.trim(),
      };
      if (editing) {
        await api(`/dye-lots/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/dye-lots', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      form = {
        ...form,
        recipeName: '',
        fabricKg: 20,
        startedAt: toLocalInput(new Date().toISOString()),
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    form = {
      vatId: String(row.vatId),
      recipeName: row.recipeName,
      fabricKg: row.fabricKg,
      startedAt: toLocalInput(row.startedAt),
      operatorName: row.operatorName,
    };
  }

  async function remove(id) {
    if (!confirm('确认删除该染程？')) return;
    error = '';
    try {
      await api(`/dye-lots/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">染程</h1>
<p class="page-sub">仅 ready / dyeing 染缸可开缸；提交后染缸自动变为染色中。</p>

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >染缸
      <select bind:value={form.vatId}>
        {#each vats as v}
          <option value={String(v.id)}
            >{v.vatCode} · {VAT_STATUS[v.status] || v.status} · {v.fiberType}</option
          >
        {/each}
      </select>
    </label>
    <label>配方名 <input bind:value={form.recipeName} /></label>
    <label>布料 kg <input type="number" step="0.1" bind:value={form.fabricKg} /></label>
    <label>开始时间 <input type="datetime-local" bind:value={form.startedAt} /></label>
    <label>操作员 <input bind:value={form.operatorName} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={save}>{editing ? '保存修改' : '新建染程'}</button>
    {#if editing}
      <button class="btn ghost" type="button" on:click={() => (editing = null)}>取消</button>
    {/if}
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

<div class="panel">
  <div class="toolbar" style="margin-bottom:0.75rem;">
    <label style="margin:0;display:flex;align-items:center;gap:0.5rem;">
      <span>按染坊筛选</span>
      <select
        bind:value={filterHouse}
        on:change={() => {
          form.vatId = '';
          load();
        }}>
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
        <th>染缸</th>
        <th>配方</th>
        <th>布料 kg</th>
        <th>开始</th>
        <th>操作员</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{vatLabel(row.vatId)}</td>
          <td>{row.recipeName}</td>
          <td>{row.fabricKg}</td>
          <td>{new Date(row.startedAt).toLocaleString()}</td>
          <td>{row.operatorName}</td>
          <td class="row-actions">
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
