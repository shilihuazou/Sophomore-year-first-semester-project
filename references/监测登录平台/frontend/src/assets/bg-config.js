/* ============================================================
 * 轮播背景照片配置（洪水监测主题）
 * 想换照片：把新图片放进 src/assets/bg/ 目录，
 * 在下面 import 并加入数组即可，顺序即播放顺序。
 * ============================================================ */
import flood1 from './bg/flood1-farmland.jpg'
import flood2 from './bg/flood2-storm.jpg'
import flood3 from './bg/flood3-dam.jpg'
import flood4 from './bg/flood4-monitor.jpg'

export const backgroundPhotos = [
  { src: flood1, title: '洪水淹没田野' },
  { src: flood2, title: '暴雨中的大坝' },
  { src: flood3, title: '水库泄洪' },
  { src: flood4, title: '水文监测站' },
]
