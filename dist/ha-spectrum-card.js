/* HA-Spectrum-Card dev prototype: real FFT only, never simulated. */
const FREQS=['31','62','125','250','500','1k','2k','4k','8k','16k'];
class HASpectrumCard extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});}
  setConfig(config){if(!config.entity)throw Error('Choose media_player entity');this.config={title:'SPECTRUM ANALYZER',spectrum_entity:'sensor.ha_spectrum_levels',...config};this.render();}
  set hass(hass){this._hass=hass;this.render();}
  getCardSize(){return 4;}
  static getConfigElement(){return document.createElement('ha-spectrum-card-editor');}
  static getStubConfig(){return {entity:'media_player.kok'};}
  escape(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  render(){
    if(!this._hass||!this.config)return;
    const player=this._hass.states[this.config.entity],spec=this._hass.states[this.config.spectrum_entity];
    const values=spec?.attributes?.levels, source=player?.attributes?.media_content_id;
    const age=Date.now()-Date.parse(spec?.attributes?.sampled_at||'');
    const valid=player?.state==='playing'&&Array.isArray(values)&&values.length===10&&
      values.every(x=>typeof x==='number'&&Number.isFinite(x))&&
      spec?.attributes?.source_entity===this.config.entity&&
      spec?.attributes?.source_media_id===source&&Number.isFinite(age)&&age>=-3000&&age<4000;
    const rows=FREQS.map((frequency,i)=>{
      const count=valid?Math.max(0,Math.min(20,Math.round(values[i]*20))):0;
      return `<div class="band"><div class="stack">${Array.from({length:20},(_,j)=>`<span class="led ${j<count?'on':''}"></span>`).reverse().join('')}</div><span>${frequency}</span></div>`;
    }).join('');
    const label=!player||player.state!=='playing'?'Standby':valid?'LIVE FFT':
      String(source||'').startsWith('spotify:')?'Spotify · FFT unavailable':'Waiting for real FFT';
    this.shadowRoot.innerHTML=`<style>
      :host{display:block}ha-card{background:#070c09;color:#c7f6d0;border:1px solid #284132;border-radius:14px;padding:16px;font-family:monospace}
      .head,.foot{display:flex;justify-content:space-between;gap:8px}.head{font-size:14px;letter-spacing:1px;margin-bottom:14px}
      .source,.foot{color:#89a995;font-size:11px}.source{max-width:45%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .bands{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:clamp(3px,1.2vw,9px)}
      .band{text-align:center;font-size:clamp(9px,1.5vw,12px);min-width:0}
      .stack{display:flex;flex-direction:column;gap:3px;margin-bottom:9px}.led{height:6px;background:#173224;border-radius:1px}
      .led.on{background:#37ee7c;box-shadow:0 0 5px #29ff76aa}.foot{margin-top:12px}
    </style><ha-card><div class="head"><span>${this.escape(this.config.title)}</span><span class="source">${this.escape(player?.attributes?.app_name||'')}</span></div>
    <div class="bands">${rows}</div><div class="foot"><span>${this.escape(label)}</span><span>Hz</span></div></ha-card>`;
  }
}
class HASpectrumCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});}
  setConfig(config){this.config=config;this.render();}
  set hass(hass){this._hass=hass;this.render();}
  render(){
    if(!this.config)return;
    const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    this.shadowRoot.innerHTML=`<div style="display:grid;gap:12px">${[['entity','Media player'],['spectrum_entity','Spectrum sensor'],['title','Title']].map(([key,label])=>`<label>${label}<input id="${key}" value="${esc(this.config[key]||'')}"></label>`).join('')}</div>`;
    for(const id of ['entity','spectrum_entity','title'])this.shadowRoot.getElementById(id).addEventListener('change',e=>{
      this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:{...this.config,[id]:e.target.value}},bubbles:true,composed:true}));
    });
  }
}
customElements.define('ha-spectrum-card',HASpectrumCard);
customElements.define('ha-spectrum-card-editor',HASpectrumCardEditor);
window.customCards=window.customCards||[];
window.customCards.push({type:'ha-spectrum-card',name:'HA Spectrum Card',description:'Real 10-band FFT audio spectrum'});
