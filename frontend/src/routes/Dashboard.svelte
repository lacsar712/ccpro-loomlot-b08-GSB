<script>
  import { onMount } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { api } from '../lib/api.js';

  let stats = null;
  let error = '';

  onMount(async () => {
    try {
      stats = await api('/dashboard/stats');
    } catch (e) {
      error = e.message;
    }
  });
</script>

<h1 class="page-title">工艺总览</h1>
<p class="page-sub">按染坊 → 染缸 → 染程 → 色牢度推进；顶部步骤条可跳转各工序。</p>

{#if error}
  <p class="err">{error}</p>
{/if}

{#if stats}
  <div class="grid-stats">
    <div class="stat">
      <div class="n">{stats.dyeHouseTotal}</div>
      <div class="l">染坊</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatReadyCount}</div>
      <div class="l">就绪染缸</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatDyeingCount}</div>
      <div class="l">染色中</div>
    </div>
    <div class="stat">
      <div class="n">{stats.lotsLast7d}</div>
      <div class="l">近 7 日染程</div>
    </div>
    <div class="stat">
      <div class="n">{stats.checksLast24h}</div>
      <div class="l">近 24 时抽检</div>
    </div>
  </div>

  <div class="panel" style="margin-bottom:1rem;">
    <p style="margin:0 0 0.75rem;font-weight:600;">各坊染缸数对照</p>
    <table>
      <thead>
        <tr>
          <th>染坊</th>
          <th>染缸数</th>
          <th>染程累计（按现属坊）</th>
        </tr>
      </thead>
      <tbody>
        {#each stats.houseVatStats as h}
          <tr>
            <td>{h.dyeHouseName}</td>
            <td>{h.vatCount}</td>
            <td>{h.dyeLotCount}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    <p style="margin:0.75rem 0 0;color:var(--indigo-mist);font-size:0.85rem;">
      染缸跨坊改挂后，两坊染缸数即时消长；染程仍挂原缸，按染缸现属坊归集。
    </p>
  </div>
{/if}

<div class="panel">
  <p style="margin:0 0 0.75rem;color:var(--indigo-mist);font-size:0.9rem;">
    业务约束：仅当染缸为 <strong>ready</strong> 或 <strong>dyeing</strong> 时可新建染程；新建后染缸自动变为 dyeing。排液可用染缸「完成排液」动作。
  </p>
  <div class="toolbar">
    <a class="btn" href="/houses" use:link>进入染坊</a>
    <a class="btn ghost" href="/vats" use:link>管理染缸</a>
    <a class="btn ghost" href="/lots" use:link>登记染程</a>
    <a class="btn ghost" href="/checks" use:link>色牢度抽检</a>
  </div>
</div>
