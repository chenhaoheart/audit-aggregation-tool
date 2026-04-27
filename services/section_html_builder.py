# -*- coding: utf-8 -*-
import json
import os
import sys

from PySide6.QtCore import QUrl

ECHARTS_CDN = "https://registry.npmmirror.com/echarts/5.5.0/files/dist/echarts.min.js"

def _get_echarts_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'assets', 'js', 'echarts.min.js')
    else:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'js', 'echarts.min.js')

_LOCAL_ECHARTS = _get_echarts_path()
ECHARTS_SRC = QUrl.fromLocalFile(_LOCAL_ECHARTS).toString() if os.path.isfile(_LOCAL_ECHARTS) else ECHARTS_CDN


CHART_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { height: 100%; overflow: hidden; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f0f4f8; color: #1f2937; }
  .container { display: flex; flex-direction: column; height: 100%; }
  .chart-row { display: flex; flex-direction: column; flex: 1; min-height: 0; }
  .chart-panel { flex: 1; display: flex; flex-direction: column; min-height: 200px; min-width: 0; }
  .chart-title { padding: 8px 12px; font-size: 13px; color: #6b7280; background: #f0f4f8; text-align: center; border-bottom: 1px solid rgba(200,200,200,0.35); flex-shrink: 0; }
  .chart-body { flex: 1; min-height: 180px; }
  .water-legend { display: flex; gap: 12px; padding: 6px 16px; font-size: 11px; color: #6b7280; border-top: 1px solid rgba(200,200,200,0.35); flex-wrap: wrap; flex-shrink: 0; }
  .water-legend .item { display: flex; align-items: center; gap: 4px; }
  .water-legend .line { width: 20px; height: 2px; border-top: 2px dashed; }
  .no-data { display: flex; align-items: center; justify-content: center; height: 100%; color: #9ca3af; font-size: 14px; }
</style>
</head>
<body>
<div class="container">
  <div class="chart-row">
    <div class="chart-panel">
      <div class="chart-title">断面形态 (起点距-高程)</div>
      <div class="chart-body" id="sectionChart"></div>
    </div>
    <div class="chart-panel">
      <div class="chart-title">测量点位置 (经度-纬度)__COORD_TITLE__</div>
      <div class="chart-body" id="coordChart"></div>
    </div>
  </div>
  <div class="water-legend" id="waterLegend">__WATER_LEGEND__</div>
</div>
<script src="__ECHARTS_SRC__"></script>
<script>
var SEC = __SEC_JSON__;
var retryCount = 0;

function safeNum(v, fallback) {
  if (v === null || v === undefined || isNaN(v)) return fallback || 0;
  return Number(v);
}

function buildSectionChartOption(sec) {
  var points = sec.points || [];
  if (points.length === 0) return {};

  var xData = [];
  var yData = [];
  for (var i = 0; i < points.length; i++) {
    var d = safeNum(points[i].distance, 0);
    var e = safeNum(points[i].elevation, 0);
    xData.push(d);
    yData.push(e);
  }

  var yMin = Math.min.apply(null, yData);
  var yMax = Math.max.apply(null, yData);
  var yPad = (yMax - yMin) * 0.15 || 1;

  var markPoints = [];
  for (var i = 0; i < points.length; i++) {
    var p = points[i];
    if (p.isFeature) {
      var seq = (p.seq != null) ? p.seq : (i + 1);
      var desc = p.feature_desc || p.feature || '';
      markPoints.push({
        coord: [safeNum(p.distance, 0), safeNum(p.elevation, 0)],
        name: '#' + seq + ' ' + desc,
        value: '#' + seq,
        itemStyle: { color: '#fb7185' },
        symbolSize: 14,
      });
    }
  }

  var series = [{
    type: 'line',
    name: '断面线',
    data: (function() {
      var arr = [];
      for (var i = 0; i < xData.length; i++) {
        arr.push([xData[i], yData[i]]);
      }
      return arr;
    })(),
    smooth: false,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { color: '#e8a838', width: 2 },
    itemStyle: { color: '#e8a838' },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(232,168,56,0.25)' },
        { offset: 1, color: 'rgba(232,168,56,0.02)' }
      ])
    },
    markPoint: {
      data: markPoints,
      symbol: 'circle',
      label: { show: true, position: 'top', fontSize: 10, color: '#fb7185', formatter: '{b}' },
    },
  }];

  var markLines = [];
  if (sec.hmz && !isNaN(sec.hmz)) {
    markLines.push({
      yAxis: sec.hmz, name: '历史最高水位',
      lineStyle: { color: '#f97316', type: 'dashed', width: 2 },
      label: { show: true, formatter: '历史最高水位 ' + Number(sec.hmz).toFixed(2) + 'm', position: 'insideEndTop', color: '#f97316', fontSize: 11 }
    });
  }
  if (sec.czz && !isNaN(sec.czz)) {
    markLines.push({
      yAxis: sec.czz, name: '成灾水位',
      lineStyle: { color: '#fb7185', type: 'dashed', width: 2 },
      label: { show: true, formatter: '成灾水位 ' + Number(sec.czz).toFixed(2) + 'm', position: 'insideEndTop', color: '#fb7185', fontSize: 11 }
    });
  }
  if (markLines.length > 0) {
    series[0].markLine = { silent: true, symbol: 'none', data: markLines };
  }

  return {
    animation: true,
    animationDuration: 600,
    grid: { left: 70, right: 20, top: 20, bottom: 45 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.92)',
      borderColor: 'rgba(200,200,200,0.40)',
      textStyle: { color: '#1f2937', fontSize: 12 },
      formatter: function(params) {
        var p = params[0];
        var idx = p.dataIndex;
        var pt = points[idx];
        if (!pt) return '';
        var html = '<b>' + (sec.name || '') + '</b><br/>';
        html += '序号: #' + (pt.seq || (idx + 1)) + '<br/>';
        html += '起点距: ' + safeNum(pt.distance, 0).toFixed(3) + ' m<br/>';
        html += '高程: ' + safeNum(pt.elevation, 0).toFixed(3) + ' m';
        if (pt.lon && pt.lat) {
          html += '<br/>经度: ' + safeNum(pt.lon, 0).toFixed(6) + '°';
          html += '<br/>纬度: ' + safeNum(pt.lat, 0).toFixed(6) + '°';
        }
        if (pt.feature_desc) html += '<br/>特征: ' + pt.feature_desc;
        else if (pt.feature) html += '<br/>特征: ' + pt.feature;
        if (pt.isFeature) html += '<br/><span style="color:#fb7185;">★ 特征点</span>';
        return html;
      }
    },
    xAxis: {
      type: 'value', name: '起点距(m)',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: '#6b7280', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(200,200,200,0.50)' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(200,200,200,0.25)' } },
    },
    yAxis: {
      type: 'value', name: '高程(m)',
      nameLocation: 'middle',
      nameGap: 50,
      nameTextStyle: { color: '#6b7280', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(200,200,200,0.50)' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(200,200,200,0.25)' } },
      min: Math.floor((yMin - yPad) * 100) / 100,
      max: Math.ceil((yMax + yPad) * 100) / 100,
    },
    series: series,
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
    ],
  };
}

function buildCoordChartOption(sec) {
  var points = sec.points || [];
  var validPoints = [];
  for (var i = 0; i < points.length; i++) {
    var p = points[i];
    if (p.lon && p.lat && !isNaN(p.lon) && !isNaN(p.lat)) {
      validPoints.push(p);
    }
  }
  if (validPoints.length === 0) return { series: [] };

  validPoints.sort(function(a, b) {
    return (a.seq || 0) - (b.seq || 0);
  });

  var lonData = [];
  var latData = [];
  for (var i = 0; i < validPoints.length; i++) {
    lonData.push(validPoints[i].lon);
    latData.push(validPoints[i].lat);
  }

  var lonMin = Math.min.apply(null, lonData);
  var lonMax = Math.max.apply(null, lonData);
  var latMin = Math.min.apply(null, latData);
  var latMax = Math.max.apply(null, latData);
  var lonPad = (lonMax - lonMin) * 0.1 || 0.001;
  var latPad = (latMax - latMin) * 0.1 || 0.001;

  var isAnomaly = sec.anomaly || false;
  var lineColor = isAnomaly ? '#fbbf24' : '#22d3ee';

  var scatterData = [];
  for (var i = 0; i < validPoints.length; i++) {
    var p = validPoints[i];
    scatterData.push({
      value: [p.lon, p.lat],
      seq: (p.seq != null) ? p.seq : (i + 1),
      distance: safeNum(p.distance, 0),
      elevation: safeNum(p.elevation, 0),
      feature: p.feature_desc || p.feature || '',
      isFeature: !!p.isFeature,
      itemStyle: { color: p.isFeature ? '#fb7185' : '#22d3ee' }
    });
  }

  var lineData = [];
  for (var i = 0; i < scatterData.length; i++) {
    lineData.push(scatterData[i].value);
  }

  return {
    animation: true,
    animationDuration: 600,
    grid: { left: 70, right: 20, top: 20, bottom: 45 },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.92)',
      borderColor: 'rgba(200,200,200,0.40)',
      textStyle: { color: '#1f2937', fontSize: 12 },
      formatter: function(params) {
        var d = params.data;
        if (!d || !d.value) return '';
        var html = '<b>测量点 #' + (d.seq || '?') + '</b><br/>';
        html += '经度: ' + d.value[0].toFixed(6) + '°<br/>';
        html += '纬度: ' + d.value[1].toFixed(6) + '°<br/>';
        html += '起点距: ' + d.distance.toFixed(3) + ' m<br/>';
        html += '高程: ' + d.elevation.toFixed(3) + ' m';
        if (d.feature) html += '<br/>特征: ' + d.feature;
        if (d.isFeature) html += '<br/><span style="color:#fb7185;">★ 特征点</span>';
        return html;
      }
    },
    xAxis: {
      type: 'value', name: '经度(°)',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: '#6b7280', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(200,200,200,0.50)' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(200,200,200,0.25)' } },
      min: Math.floor((lonMin - lonPad) * 1000000) / 1000000,
      max: Math.ceil((lonMax + lonPad) * 1000000) / 1000000,
    },
    yAxis: {
      type: 'value', name: '纬度(°)',
      nameLocation: 'middle',
      nameGap: 50,
      nameTextStyle: { color: '#6b7280', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(200,200,200,0.50)' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(200,200,200,0.25)' } },
      min: Math.floor((latMin - latPad) * 1000000) / 1000000,
      max: Math.ceil((latMax + latPad) * 1000000) / 1000000,
    },
    series: [
      {
        type: 'line',
        name: '测量轨迹',
        data: lineData,
        smooth: false,
        symbol: 'none',
        lineStyle: { color: lineColor, width: 2, type: isAnomaly ? 'dashed' : 'solid' },
        tooltip: { show: false }
      },
      {
        type: 'scatter',
        name: '测量点',
        data: scatterData,
        symbolSize: 8,
        label: {
          show: true,
          position: 'right',
          color: '#6b7280',
          fontSize: 10,
          formatter: function(params) { return '#' + (params.data.seq || '?'); }
        },
        itemStyle: { borderColor: '#fff', borderWidth: 1 },
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
      { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
    ],
  };
}

function initCharts() {
  if (typeof echarts === 'undefined') {
    if (retryCount < 3) {
      retryCount++;
      document.getElementById('sectionChart').innerHTML = '<div class="no-data">ECharts 加载中... (重试 ' + retryCount + '/3)</div>';
      setTimeout(initCharts, 1500);
      return;
    }
    document.getElementById('sectionChart').innerHTML = '<div class="no-data">ECharts 加载失败，请检查网络连接或将 echarts.min.js 放到 assets/js/ 目录下</div>';
    return;
  }
  var secDom = document.getElementById('sectionChart');
  var coordDom = document.getElementById('coordChart');
  if (!secDom || !coordDom) return;

  if (secDom.clientHeight < 10 || secDom.clientWidth < 10) {
    setTimeout(initCharts, 200);
    return;
  }

  var secChart = echarts.init(secDom, null, {renderer: 'canvas'});
  var secOption = buildSectionChartOption(SEC);
  if (secOption && secOption.series && secOption.series.length > 0) {
    secChart.setOption(secOption);
  } else {
    secDom.innerHTML = '<div class="no-data">无断面数据</div>';
  }

  var coordChart = null;
  var coordOption = buildCoordChartOption(SEC);
  if (coordOption.series && coordOption.series.length > 0) {
    coordChart = echarts.init(coordDom, null, {renderer: 'canvas'});
    coordChart.setOption(coordOption);
  } else {
    coordDom.innerHTML = '<div class="no-data">无经纬度数据</div>';
  }

  window.addEventListener('resize', function() {
    secChart.resize();
    try { coordChart && coordChart.resize(); } catch(e) {}
  });
}

if (typeof echarts !== 'undefined') {
  initCharts();
} else {
  document.getElementById('sectionChart').innerHTML = '<div class="no-data">ECharts 加载中...</div>';
  var script = document.querySelector('script[src*="echarts"]');
  if (script) {
    script.onload = function() { retryCount = 0; initCharts(); };
    script.onerror = function() {
      var fallback = document.createElement('script');
      fallback.src = '__ECHARTS_CDN__';
      fallback.onload = function() { retryCount = 0; initCharts(); };
      fallback.onerror = function() { initCharts(); };
      document.head.appendChild(fallback);
    };
  }
  setTimeout(initCharts, 3000);
}
</script>
</body>
</html>"""


def _clean_points_for_json(points):
    cleaned = []
    for p in points:
        pt = {}
        for k in ("seq", "distance", "elevation", "lon", "lat", "feature_desc", "feature", "isFeature", "roughness"):
            v = p.get(k)
            if v is None:
                continue
            pt[k] = v
        if "distance" not in pt and "elevation" not in pt:
            continue
        cleaned.append(pt)
    return cleaned


def generate_chart_html(sec: dict) -> str:
    has_coords = any(p.get("lon") and p.get("lat") for p in sec.get("points", []))
    coord_title_suffix = " ⚠ 经纬度连线异常" if sec.get("anomaly") else ""
    if not has_coords:
        coord_title_suffix = " (无经纬度数据)"

    legend_items = []
    if sec.get("hmz"):
        legend_items.append(
            f'<div class="item"><div class="line" style="border-color:#f97316;"></div>历史最高水位 {sec["hmz"]:.2f}m</div>'
        )
    if sec.get("czz"):
        legend_items.append(
            f'<div class="item"><div class="line" style="border-color:#fb7185;"></div>成灾水位 {sec["czz"]:.2f}m</div>'
        )

    sec_json_data = {
        "name": sec.get("name", ""),
        "hmz": sec.get("hmz"),
        "czz": sec.get("czz"),
        "anomaly": sec.get("anomaly", False),
        "points": _clean_points_for_json(sec.get("points", [])),
    }

    html = CHART_HTML_TEMPLATE
    html = html.replace("__ECHARTS_SRC__", ECHARTS_SRC)
    html = html.replace("__ECHARTS_CDN__", ECHARTS_CDN)
    html = html.replace("__SEC_JSON__", json.dumps(sec_json_data, ensure_ascii=False, default=str))
    html = html.replace("__COORD_TITLE__", coord_title_suffix)
    html = html.replace("__WATER_LEGEND__", "".join(legend_items))
    return html
