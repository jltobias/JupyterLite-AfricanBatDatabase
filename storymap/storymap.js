"use strict";

const radii = [1, 5, 10, 20, 30, 40, 50];
const radiusColors = ["#d46149", "#d88b48", "#c5a345", "#81934d", "#588c6f", "#3f7d7a", "#385e78"];
const map = L.map("map", { scrollWheelZoom: false }).setView([4, 17], 4);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
}).addTo(map);

const facilityLayer = L.layerGroup().addTo(map);
const recordLayer = L.layerGroup().addTo(map);
const ringLayer = L.layerGroup().addTo(map);
let story;
let currentIndex = 0;
let visiblePages = [];
let selectedRecord;
const enabledRadii = new Set();
const status = document.getElementById("status");

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

function link(url, label) {
  if (!url) return "";
  return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`;
}

function localPhoto(filename) {
  return filename ? `assets/photos/${encodeURIComponent(filename)}` : "";
}

function buildRadiusControls() {
  const container = document.getElementById("radius-controls");
  container.replaceChildren();
  radii.forEach((radius, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "radius-button";
    button.textContent = `${radius} km`;
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      if (enabledRadii.has(radius)) enabledRadii.delete(radius);
      else enabledRadii.add(radius);
      button.setAttribute("aria-pressed", String(enabledRadii.has(radius)));
      drawRings();
    });
    button.style.setProperty("--ring-color", radiusColors[index]);
    container.appendChild(button);
  });
  document.querySelectorAll('input[name="ring-center"]').forEach((input) => {
    input.addEventListener("change", drawRings);
  });
}

function drawRings() {
  ringLayer.clearLayers();
  if (!story || !story.pages[currentIndex]) return;
  const centerMode = document.querySelector('input[name="ring-center"]:checked').value;
  const coordinates = centerMode === "bat" && selectedRecord
    ? selectedRecord.coordinates
    : story.pages[currentIndex].coordinates;
  if (centerMode === "bat" && !selectedRecord) return;
  const [longitude, latitude] = coordinates;
  radii.forEach((radius, index) => {
    if (!enabledRadii.has(radius)) return;
    L.circle([latitude, longitude], {
      radius: radius * 1000,
      color: radiusColors[index],
      fill: false,
      opacity: 0.8,
      weight: 1.5
    }).bindTooltip(`${radius} km ${centerMode === "bat" ? "from selected bat record" : "from facility"}`)
      .addTo(ringLayer);
  });
}

function groupedRecords(page) {
  const sites = new Map();
  page.bat_records.forEach((record) => {
    const key = `${record.coordinates[0]},${record.coordinates[1]}`;
    if (!sites.has(key)) sites.set(key, { coordinates: record.coordinates, records: [] });
    sites.get(key).records.push(record);
  });
  return Array.from(sites.values());
}

function speciesCard(record) {
  selectedRecord = record;
  const image = record.image
    ? `<img class="species-photo" src="${localPhoto(record.image)}" alt="${esc(record.scientific_name)}">`
    : "";
  const photoCredit = record.image
    ? `<span class="photo-credit">${esc(record.image_credit || "Photo credit unavailable")} · ${link(record.image_source, "image source")}</span>`
    : "";
  const english = record.english_name || "Common name not yet verified";
  const diet = record.diet
    ? `${esc(record.diet)} ${link(record.diet_source, "source")}`
    : "No species-specific diet source has been reviewed for this record.";
  const foraging = record.foraging_range
    ? `${esc(record.foraging_range)} ${link(record.foraging_source, "source")}`
    : "No quantified foraging range is asserted. Buffer radii are analysis distances, not foraging estimates.";
  document.getElementById("species-card").innerHTML = `
    ${image}${photoCredit}
    <h3>${esc(english)}</h3>
    <div class="scientific-name">${esc(record.scientific_name || "Scientific name not recorded")}</div>
    <dl>
      <dt>Record locality</dt><dd>${esc(record.location || "Not recorded")}, ${esc(record.country || "")}</dd>
      <dt>Record year</dt><dd>${esc(record.year || "Not recorded")}</dd>
      <dt>Common name source</dt><dd>${link(record.name_source, "species account")}</dd>
      <dt>Distance to facility</dt><dd>${Number(record.distance_km).toFixed(2)} km (${esc(record.distance_band)})</dd>
      <dt>Diet</dt><dd>${diet}</dd>
      <dt>Foraging</dt><dd>${foraging}</dd>
      <dt>Record source</dt><dd>${esc(record.reference || "Database reference not recorded")} · ${link("https://doi.org/10.6084/m9.figshare.26363308.v1", "dataset citation")}</dd>
    </dl>
    <p class="disease-note">${esc(record.disease_note || "No disease transmission or mine-related health claim is inferred from spatial proximity.")}</p>`;
  drawRings();
}

function selectSite(site, scroll = false) {
  const firstRecord = site.records[0];
  if (firstRecord) speciesCard(firstRecord);
  recordLayer.eachLayer((layer) => {
    if (layer.options.recordIds?.includes(firstRecord?.record_id)) layer.openTooltip();
  });
  if (scroll) document.getElementById("species-card").scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function renderBands(page) {
  const container = document.getElementById("distance-bands");
  container.replaceChildren();
  const values = Object.entries(page.band_counts);
  const maximum = Math.max(1, ...values.map((entry) => entry[1]));
  values.forEach(([band, count]) => {
    const row = document.createElement("div");
    row.className = "band-row";
    row.innerHTML = `<span>${esc(band)}</span><div class="band-track"><div class="band-fill" style="width:${count / maximum * 100}%"></div></div><span class="band-count">${count}</span>`;
    container.appendChild(row);
  });
}

function initializeMineFilters() {
  const countryFilter = document.getElementById("country-filter");
  const mineFilter = document.getElementById("mine-filter");
  const allCountries = document.createElement("option");
  allCountries.value = "";
  allCountries.textContent = "All countries";
  countryFilter.appendChild(allCountries);

  const countries = [...new Set(
    story.pages.map((page) => page.facility.country).filter(Boolean)
  )].sort((a, b) => a.localeCompare(b));
  countries.forEach((country) => {
    const option = document.createElement("option");
    option.value = country;
    option.textContent = country;
    countryFilter.appendChild(option);
  });
  countryFilter.value = story.pages[0]?.facility.country || "";

  function updateMineOptions() {
    visiblePages = story.pages
      .map((page, storyIndex) => ({ page, storyIndex }))
      .filter(({ page }) => !countryFilter.value || page.facility.country === countryFilter.value);
    mineFilter.replaceChildren();

    const nameCounts = new Map();
    visiblePages.forEach(({ page }) => {
      const name = page.facility.name || "Unnamed facility";
      nameCounts.set(name, (nameCounts.get(name) || 0) + 1);
    });
    visiblePages.forEach(({ page, storyIndex }) => {
      const option = document.createElement("option");
      option.value = String(storyIndex);
      const name = page.facility.name || "Unnamed facility";
      option.textContent = nameCounts.get(name) > 1
        ? `${name} · USGS ${page.facility.source_position}`
        : name;
      mineFilter.appendChild(option);
    });
    renderPage(0);
  }

  countryFilter.addEventListener("change", updateMineOptions);
  mineFilter.addEventListener("change", () => {
    const storyIndex = Number(mineFilter.value);
    const pageIndex = visiblePages.findIndex((entry) => entry.storyIndex === storyIndex);
    if (pageIndex >= 0) renderPage(pageIndex);
  });
  updateMineOptions();
}

function renderPage(index) {
  if (!story || !visiblePages.length) {
    status.textContent = "No coordinate-valid mine facilities have bat records within 50 km in the selected sources.";
    return;
  }
  currentIndex = Math.max(0, Math.min(index, visiblePages.length - 1));
  const { page, storyIndex } = visiblePages[currentIndex];
  document.getElementById("mine-filter").value = String(storyIndex);
  selectedRecord = undefined;
  facilityLayer.clearLayers();
  recordLayer.clearLayers();
  ringLayer.clearLayers();
  const [mineLon, mineLat] = page.coordinates;
  L.circleMarker([mineLat, mineLon], {
    radius: 8, color: "#8e3c2d", weight: 2, fillColor: "#c85e47", fillOpacity: 1
  }).bindTooltip(esc(page.facility.name), { permanent: false })
    .bindPopup(`<strong>${esc(page.facility.name)}</strong><br>${esc(page.facility.country)} · ${esc(page.facility.commodity || "commodity not recorded")}`)
    .addTo(facilityLayer);

  const sites = groupedRecords(page);
  sites.forEach((site) => {
    const [lon, lat] = site.coordinates;
    const names = site.records.map((record) => record.scientific_name).filter(Boolean);
    const marker = L.circleMarker([lat, lon], {
      radius: 5, color: "#6d5824", weight: 1.5, fillColor: "#ddb95f", fillOpacity: .92,
      recordIds: site.records.map((record) => record.record_id)
    });
    marker.bindTooltip(names.map(esc).join("<br>"), { direction: "top", opacity: .95 });
    marker.on("mouseover", () => selectSite(site));
    marker.on("click", () => selectSite(site, true));
    marker.addTo(recordLayer);
  });

  const facilityPhoto = page.facility.name.toLowerCase().includes("ouenza")
    ? ["ouenza-mine.jpg", "Michkar, CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:196104-ouenza-mine-de-fer-02.jpg"]
    : page.facility.name.toLowerCase().includes("kherzet youcef")
      ? ["kherzet-youcef-mine.jpg", "Missaad, CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Puits_n%C2%B03_de_la_mine_de_Kherzet_Youcef.jpg"]
      : null;
  const picture = facilityPhoto
    ? `<img class="facility-photo" src="${localPhoto(facilityPhoto[0])}" alt="Photograph of ${esc(page.facility.name)}">`
    : `<p class="control-note">No verified site photograph is available for this facility.</p>`;
  const pictureCredit = facilityPhoto
    ? `<span class="photo-credit">${esc(facilityPhoto[1])} · ${link(facilityPhoto[2], "photo source")}</span>`
    : "";
  document.getElementById("facility-card").innerHTML = `
    ${picture}${pictureCredit}
    <div class="facility-heading"><h2>${esc(page.facility.name)}</h2><span class="status-pill">${esc(page.facility.status || "Status not recorded")}</span></div>
    <div class="facility-facts">
      <div><dt>Country</dt><dd>${esc(page.facility.country)}</dd></div>
      <div><dt>Commodity</dt><dd>${esc(page.facility.commodity || "Not recorded")}</dd></div>
      <div><dt>Facility type</dt><dd>${esc(page.facility.facility_type || "Not recorded")}</dd></div>
      <div><dt>Mining method</dt><dd>${esc(page.facility.mining_method || "Not recorded")}</dd></div>
      <div><dt>Operator</dt><dd>${esc(page.facility.operator || "Not recorded")}</dd></div>
      <div><dt>Capacity (2006)</dt><dd>${esc(page.facility.capacity || "Not recorded")} ${esc(page.facility.units || "")}</dd></div>
    </div>
    <p><strong>${page.nearby_record_count}</strong> bat point records within 50 km; nearest record ${Number(page.nearest_record_km).toFixed(2)} km away.</p>`;

  document.getElementById("record-count").textContent = `(${page.bat_records.length})`;
  const list = document.getElementById("record-list");
  list.replaceChildren();
  page.bat_records.forEach((record) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.innerHTML = `<em>${esc(record.scientific_name || "Unknown species")}</em><span>${Number(record.distance_km).toFixed(1)} km</span>`;
    button.addEventListener("mouseenter", () => speciesCard(record));
    button.addEventListener("focus", () => speciesCard(record));
    button.addEventListener("click", () => {
      speciesCard(record);
      document.querySelectorAll(".record-list button").forEach((candidate) => candidate.removeAttribute("aria-current"));
      button.setAttribute("aria-current", "true");
    });
    item.appendChild(button);
    list.appendChild(item);
  });
  if (page.bat_records.length) speciesCard(page.bat_records[0]);
  renderBands(page);
  document.getElementById("page-number").textContent = `${currentIndex + 1} / ${visiblePages.length}`;
  document.getElementById("previous").disabled = currentIndex === 0;
  document.getElementById("next").disabled = currentIndex === visiblePages.length - 1;
  status.textContent = `${story.summary.valid_bat_records.toLocaleString()} valid point records · ${story.summary.invalid_bat_coordinates_excluded} invalid source coordinates excluded · source precision retained`;
  map.setView([mineLat, mineLon], 8);
  drawRings();
}

document.getElementById("previous").addEventListener("click", () => renderPage(currentIndex - 1));
document.getElementById("next").addEventListener("click", () => renderPage(currentIndex + 1));
buildRadiusControls();

fetch("data/storymap.json")
  .then((response) => {
    if (!response.ok) throw new Error(`Could not load story data (${response.status}).`);
    return response.json();
  })
  .then((data) => {
    story = data;
    initializeMineFilters();
  })
  .catch((error) => {
    status.textContent = `StoryMap data error: ${error.message}`;
    console.error(error);
  });
