/** Front-end da demonstração. Sem bibliotecas de UI ou dependências externas. */
const state = { orders: [], selectedId: null, latestRequest: 0 };
const ui = {
  search: document.querySelector('#filter'),
  tableBody: document.querySelector('#orders'),
  selected: document.querySelector('#selected'),
  note: document.querySelector('#note'),
  result: document.querySelector('#result'),
  runButton: document.querySelector('#run'),
};

function percentage(value) {
  return `${Math.round(value * 100)}%`;
}

function makeElement(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = String(value);
  return element;
}

function selectOrder(orderId) {
  state.selectedId = orderId;
  ui.selected.textContent = `Pedido selecionado: ${orderId}`;
  ui.tableBody.querySelectorAll('tr').forEach((row) => {
    const active = row.dataset.id === orderId;
    row.classList.toggle('selected', active);
    row.setAttribute('aria-selected', active ? 'true' : 'false');
  });
}

function makeRow(order) {
  const row = makeElement('tr');
  row.dataset.id = order.order_id;
  row.tabIndex = 0;

  row.append(makeElement('td', 'id', order.order_id));
  const risk = makeElement('td');
  const label = makeElement('div', `risk ${order.risk_label === 'Alto' ? 'high' : 'low'}`, percentage(order.risk));
  const bar = makeElement('span', 'riskbar');
  const progress = document.createElement('i');
  progress.style.width = `${Math.min(100, Math.max(0, order.risk * 100))}%`;
  bar.append(progress);
  label.append(bar);
  risk.append(label);
  row.append(risk);
  row.append(makeElement('td', null, order.weather));
  row.append(makeElement('td', null, `${order.distance_km.toFixed(1)} km`));
  row.append(makeElement('td', null, order.kitchen_queue));

  const handleSelect = () => { selectOrder(order.order_id); analyzeOrder(); };
  row.addEventListener('click', handleSelect);
  row.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleSelect();
    }
  });
  return row;
}

function renderOrders() {
  const query = ui.search.value.trim().toLowerCase();
  const visible = state.orders.filter((order) => order.order_id.toLowerCase().includes(query));
  ui.tableBody.replaceChildren(...visible.map(makeRow));
  if (state.selectedId) selectOrder(state.selectedId);
}

function showTriage(data) {
  const message = makeElement('p', null, data.message || 'Sem explicação disponível.');
  const chips = makeElement('div', 'chips');
  for (const action of data.actions || []) {
    chips.append(makeElement('span', 'chip', action.replaceAll('_', ' ')));
  }
  const evidences = (data.citations || []).map((citation) => {
    const wrapper = makeElement('div', 'evidence');
    wrapper.append(makeElement('b', null, `[${citation.id}] ${citation.title} · similaridade ${citation.score}`));
    wrapper.append(makeElement('p', null, citation.text));
    return wrapper;
  });
  // textContent evita interpretar qualquer texto de resposta como HTML.
  ui.result.replaceChildren(message, chips, ...evidences);
}

async function fetchJson(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data;
}

async function analyzeOrder() {
  if (!state.selectedId) return;
  const requestId = ++state.latestRequest;
  ui.runButton.disabled = true;
  ui.result.textContent = 'Analisando o pedido e consultando as políticas…';

  try {
    const data = await fetchJson(`/api/triage/${encodeURIComponent(state.selectedId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: ui.note.value, mode: 'offline' }),
    });
    // Uma resposta mais antiga não deve substituir a triagem do novo pedido.
    if (requestId === state.latestRequest) showTriage(data);
  } catch (error) {
    if (requestId === state.latestRequest) {
      ui.result.textContent = `Não foi possível analisar o pedido: ${error.message}`;
    }
  } finally {
    if (requestId === state.latestRequest) ui.runButton.disabled = false;
  }
}

async function initialize() {
  ui.search.addEventListener('input', renderOrders);
  ui.runButton.addEventListener('click', analyzeOrder);
  try {
    const [ordersData, metricsData] = await Promise.all([
      fetchJson('/api/orders'),
      fetchJson('/api/metrics'),
    ]);
    state.orders = ordersData.orders;
    document.querySelector('#all').textContent = state.orders.length;
    document.querySelector('#high').textContent = state.orders.filter((order) => order.risk_label === 'Alto').length;
    document.querySelector('#auc').textContent = metricsData.model.roc_auc.toFixed(3);
    document.querySelector('#recall').textContent = percentage(metricsData.model.recall);
    renderOrders();
    if (state.orders.length) {
      selectOrder(state.orders[0].order_id);
      await analyzeOrder();
    }
  } catch (error) {
    ui.result.textContent = `Falha ao carregar a demonstração: ${error.message}. Execute python scripts/train.py.`;
  }
}

initialize();
