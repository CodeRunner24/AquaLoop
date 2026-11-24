const byId = (id) => document.getElementById(id);
const setText = (id, value) => { byId(id).textContent = value; };
const delayText = (value) => value === null ? 'Alarm oluşmadı' : value === 0 ? 'Başlangıçta' : `${fmt(value, 0)} saat sonra`;
const processOptions = [PROCESS.summary.normal, ...PROCESS.summary.events];
const processColors = ['#008c91', '#8aa8bc'];

function energyIntensity(rows, energyKey, volumeKey) {
  const energy = rows.reduce((sum, row) => sum + row[energyKey], 0);
  const volume = rows.reduce((sum, row) => sum + row[volumeKey], 0);
  return volume > 0 ? `${fmt(energy / volume, 2)} kWh/m³` : '—';
}

function drawProcessPanel() {
  const selected = processOptions.find((option) => option.id === byId('processEvent').value);
  const isEvent = selected.id !== 'normal';
  const window = PROCESS.rows.slice(selected.window_start, selected.window_end);
  const measuredPeriod = isEvent ? PROCESS.rows.slice(selected.start, selected.end) : window;
  const status = byId('processStatus');
  const hasAlarm = measuredPeriod.some((row) => row.ai_alarm);
  status.classList.toggle('ops-alert', hasAlarm);
  status.textContent = hasAlarm ? 'İnceleme uyarısı · debi ve pompa/filtre hattını kontrol edin.' : 'Seçili kesitte model uyarısı yok.';

  const location = `Testin ${selected.window_start + 1}–${selected.window_end}. saatleri`;
  const faultTimes = isEvent ? ` · sentetik arızanın başladığı saat ${selected.start + 1}` : '';
  setText('processWindow', `${location}${faultTimes}`);
  setText('eventFixedDelay', isEvent ? delayText(selected.fixed_delay) : 'Normal kesit');
  setText('eventAiDelay', isEvent ? delayText(selected.ai_delay) : 'Normal kesit');
  setText('eventIntensity', energyIntensity(measuredPeriod, 'pump_kwh', 'treated_m3'));
  setText('expectedIntensity', energyIntensity(measuredPeriod, 'expected_kwh', 'expected_m3'));

  const markers = [];
  if (isEvent) {
    markers.push({ index: selected.start - selected.window_start, color: '#a0392b', label: 'Arıza' });
    if (selected.ai_delay !== null) {
      markers.push({ index: selected.start + selected.ai_delay - selected.window_start, color: '#006c71', label: 'Alarm' });
    }
  }
  canvasChart('processFlowChart', [window.map((row) => row.treated_m3), window.map((row) => row.expected_m3)], processColors, window.length, markers);
  canvasChart('processPowerChart', [window.map((row) => row.pump_kwh), window.map((row) => row.expected_kwh)], processColors, window.length, markers);
}

function setupProcessPanel() {
  const select = byId('processEvent');
  for (const event of processOptions) {
    const option = document.createElement('option');
    option.value = event.id;
    option.textContent = event.name;
    select.append(option);
  }
  select.value = PROCESS.summary.events[0].id;
  select.addEventListener('change', drawProcessPanel);
  for (const key of ['fixed', 'ai']) {
    const result = PROCESS.summary.detectors[key];
    setText(key + 'Found', `${result.detected}/${result.total_events}`);
    setText(key + 'False', `${result.false_alarm_hours} saat`);
    setText(key + 'Mean', result.mean_delay_h === null ? '—' : `${fmt(result.mean_delay_h, 2)} saat`);
  }
  const buildingAlarm = PROCESS.building_alarm;
  if (buildingAlarm) {
    setText('buildingFirst', `Testin ${fmt(buildingAlarm.first_hour, 0)}. saati`);
    setText('buildingDuration', `${fmt(buildingAlarm.duration_h, 0)} saat`);
    setText('buildingExcess', `${fmt(buildingAlarm.estimated_excess_l, 0)} L`);
  }
  document.querySelector('[data-tab="operations"]').addEventListener('click', drawProcessPanel);
  window.addEventListener('resize', () => {
    if (byId('operations').classList.contains('active')) drawProcessPanel();
  });
  drawProcessPanel();
}

const heatFields = {
  capex: 'heatCapex', heatPrice: 'heatPrice', maintenance: 'heatMaintenance', aux: 'heatAux',
  powerPrice: 'heatPowerPrice', days: 'heatDays', demandShare: 'heatDemandShare', overlap: 'heatOverlap',
  setpoint: 'heatSetpoint', efficiency: 'heatEfficiency',
};
const heatOutputFields = ['annualPotential', 'annualUseful', 'annualGross', 'annualOpex', 'annualNet'];

function calculateHeatPayback(data, inputs) {
  const heatCapacity = 1000 * 4.186 / 3600; // kWh/(m³·°C)
  let potential = 0;
  let useful = 0;
  for (const row of data) {
    const sourceDelta = Math.max(0, row.wastewater_temp_c - row.cold_inlet_temp_c);
    const coincidentVolume = row.total_water_m3 * inputs.demandShare * inputs.overlap / 10000;
    const exchangerKwhPerM3 = heatCapacity * sourceDelta * inputs.efficiency / 100;
    const transferable = Math.min(row.greywater_in_m3, coincidentVolume) * exchangerKwhPerM3;
    const demand = coincidentVolume * heatCapacity * Math.max(0, inputs.setpoint - row.cold_inlet_temp_c);
    potential += row.greywater_in_m3 * exchangerKwhPerM3;
    useful += Math.min(transferable, demand);
  }
  const scale = inputs.days / (data.length / 24);
  const annualPotential = potential * scale;
  const annualUseful = useful * scale;
  const annualGross = annualUseful * inputs.heatPrice;
  const annualOpex = inputs.maintenance + inputs.aux * inputs.days * inputs.powerPrice;
  const annualNet = annualGross - annualOpex;
  return { annualPotential, annualUseful, annualGross, annualOpex, annualNet, years: annualNet > 0 ? inputs.capex / annualNet : null };
}

function updateHeatPayback() {
  const fields = Object.values(heatFields).map(byId);
  if (fields.some((field) => !field.validity.valid)) {
    setText('heatPayback', '—');
    setText('heatPaybackNote', 'Hesap için tüm değerleri alanlardaki geçerli aralıkta girin.');
    heatOutputFields.forEach((id) => setText(id, '—'));
    return;
  }
  const inputs = Object.fromEntries(Object.entries(heatFields).map(([key, id]) => [key, byId(id).valueAsNumber]));
  const result = calculateHeatPayback(DATA, inputs);
  setText('heatPayback', result.years === null ? 'Geri ödeme oluşmuyor' : `${fmt(result.years, 2)} yıl`);
  setText('heatPaybackNote', result.years === null ? 'Bu senaryoda net yıllık fayda pozitif değil.' : 'Girilen varsayımlarla hesaplanan, iskonto edilmemiş süre.');
  for (const id of heatOutputFields) {
    const unit = id === 'annualPotential' || id === 'annualUseful' ? 'kWh ısı/yıl' : 'TL/yıl';
    setText(id, `${fmt(result[id], 0)} ${unit}`);
  }
}

function setupPaybackPanel() {
  const form = byId('heatForm');
  form.addEventListener('submit', (event) => { event.preventDefault(); updateHeatPayback(); });
  form.addEventListener('input', (event) => {
    if (event.target.id === 'heatEfficiency' && event.target.validity.valid) {
      byId('eff').value = event.target.value;
      setText('effLabel', `${event.target.value}%`);
      render();
    }
    updateHeatPayback();
  });
  byId('eff').addEventListener('input', (event) => {
    byId('heatEfficiency').value = event.target.value;
    updateHeatPayback();
  });
  updateHeatPayback();
}

setupProcessPanel();
setupPaybackPanel();
