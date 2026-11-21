/* N.I. SINOTTICA: optional terrain annotations, Natural Earth data.
   Include after Leaflet and after the map variable is initialized.
   Elevation points are NOT a continuous elevation model or hillshade. */
(async function addElevationPoints(){
  const pane=map.createPane('niElevations');
  pane.style.zIndex=225;
  const r=await fetch('data/cartografia/elevation_points.geojson');
  if(!r.ok)throw new Error('Natural Earth elevations unavailable');
  const geo=await r.json();
  const layer=L.geoJSON(geo,{
    pane:'niElevations',
    filter:f=>f.geometry?.type==='Point',
    pointToLayer:(f,ll)=>L.circleMarker(ll,{
      pane:'niElevations',radius:3,weight:1,color:'#53646b',
      fillColor:'#c8c4b8',fillOpacity:.9
    }),
    onEachFeature:(f,l)=>{
      const p=f.properties||{};
      const name=p.name||p.NAME||'Rilievo';
      const h=p.elevation||p.ELEVATION||p.elev||p.ELEV||'';
      l.bindPopup(String(name)+(h?' · '+h+' m':''));
    }
  }).addTo(map);
  window.niElevationLayer=layer;
})().catch(console.warn);
