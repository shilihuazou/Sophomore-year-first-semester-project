<script setup>
defineEmits(["change-password", "sign-out"]);
</script>

<template>
  <header class="topbar">
    <div class="brand-line">
      <div class="brand-icon">KQ</div>
      <div>
        <span class="system-kicker">KQGIS GEOHAZARD RESPONSE</span>
        <strong
          >基于KQGIS的地质灾害监测救援部署系统—以吉隆口岸泥石流灾害为例</strong
        >
      </div>
    </div>
    <div class="top-account">
      <button class="password-action" @click="$emit('change-password')">
        修改密码
      </button>
      <button class="sign-out-action" @click="$emit('sign-out')">退出</button>
    </div>
  </header>
</template>
