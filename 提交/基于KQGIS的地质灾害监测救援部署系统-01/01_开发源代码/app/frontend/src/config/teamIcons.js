export const TEAM_ICON_SYMBOLS = Object.freeze({
  抢险救援组:
    '<path d="M14 14l15 15M29 14L14 29" fill="none" stroke="white" stroke-width="3.2" stroke-linecap="round"/><path d="M11.5 11.5l6.5 1.8-4.7 4.7zM31.5 11.5L25 13.3l4.7 4.7z" fill="white"/>',
  医疗治疗组:
    '<path d="M18.2 9.5h7.6v8.7h8.7v7.6h-8.7v8.7h-7.6v-8.7H9.5v-7.6h8.7z" fill="white"/>',
  电力保障组:
    '<path d="M25.4 7.5L11.8 24h9l-2.2 12.5L33 17.8h-9.2z" fill="white"/>',
  地质监测组:
    '<path d="M8.5 32l9.8-17.5 5.7 9 4.8-6.6L35.5 32z" fill="none" stroke="white" stroke-width="2.7" stroke-linejoin="round"/><path d="M11.5 28.5h21M14 24.5h6.5M27 24.5h4" fill="none" stroke="white" stroke-width="2" stroke-linecap="round"/><circle cx="29" cy="12" r="2.6" fill="white"/>',
  群众安置组:
    '<path d="M8.5 21.5L22 10.7l13.5 10.8M12.5 20v14h19V20M19 34v-8h6v8" fill="none" stroke="white" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="22" cy="19.5" r="2.4" fill="white"/>',
});

export const TEAM_ICON_COLORS = Object.freeze({
  抢险救援组: "#bd3b46",
  医疗治疗组: "#d34a6a",
  电力保障组: "#d88a19",
  地质监测组: "#327963",
  群众安置组: "#3f70a5",
});

export function resolveTeamCategory(teamName = "") {
  if (teamName.startsWith("抢险救援")) return "抢险救援组";
  if (teamName.startsWith("医疗治疗")) return "医疗治疗组";
  if (teamName.startsWith("电力保障")) return "电力保障组";
  if (teamName.startsWith("地质监测")) return "地质监测组";
  if (teamName.startsWith("群众安置")) return "群众安置组";
  return "";
}
