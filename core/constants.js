export const DEFAULT_DIR = 'C:\\Users\\chenh\\Desktop\\青海24示范小流域-药草沟-20260313'

export const GEOMETRY_ORDER_VALUE = { 'Polygon': 0, 'Line': 5, 'Point': 10 }

export const TIANDITU_KEY = 'fced2cd1905b5b42d4167603c6ba32e2'

export const TIANDITU_LAYERS = {
  img: {
    name: '影像地图',
    base: `https://t{s}.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TIANDITU_KEY}`,
    label: `https://t{s}.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TIANDITU_KEY}`,
  },
  vec: {
    name: '矢量地图',
    base: `https://t{s}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TIANDITU_KEY}`,
    label: `https://t{s}.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TIANDITU_KEY}`,
  },
  ter: {
    name: '地形地图',
    base: `https://t{s}.tianditu.gov.cn/ter_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ter&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TIANDITU_KEY}`,
    label: `https://t{s}.tianditu.gov.cn/cta_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cta&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TIANDITU_KEY}`,
  },
}

export const GEOMETRY_STYLE_MAP = {
  Point: { radius: 6, fillOpacity: 0.8, weight: 2 },
  Line: { weight: 3, opacity: 0.8, dashArray: null },
  Polygon: { weight: 2, fillOpacity: 0.25, opacity: 0.8 },
}

export const GEOMETRY_ICONS = {
  Point: 'Circle',
  Line: 'Minus',
  Polygon: 'Square',
}

export const FILL_STYLES = [
  { value: 'solid', label: '实心填充' },
  { value: 'hollow', label: '空心边框' },
  { value: 'transparent', label: '半透明' },
  { value: 'dashed', label: '虚线边框' },
]

export const ADMIN_LEVELS = [
  { value: 2, label: '省级（前2位）' },
  { value: 4, label: '市级（前4位）' },
  { value: 6, label: '县级（前6位）' },
]
