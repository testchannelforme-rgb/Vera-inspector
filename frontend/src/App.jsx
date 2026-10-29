import React,{useEffect,useRef,useState} from 'react';
import Brand from './components/Brand.jsx';
import Icon from './components/Icon.jsx';
import Landing from './components/Landing.jsx';
import InspectorWorkspace from './components/InspectorWorkspace.jsx';
import InfoPage from './components/InfoPage.jsx';
import DataPreferences from './components/DataPreferences.jsx';
import {routeFromHash} from './router.js';
export default function App(){
  const [route,setRoute]=useState(()=>routeFromHash(globalThis.location?.hash)),[menu,setMenu]=useState(false),[visited,setVisited]=useState(()=>routeFromHash(globalThis.location?.hash).page==='inspector'),[replay,setReplay]=useState(0),[preferencesEpoch,setPreferencesEpoch]=useState(0);
  const main=useRef(null),lastPage=useRef(route.page);
  useEffect(()=>{const change=()=>{const next=routeFromHash(window.location.hash);setRoute(next);setMenu(false);if(next.page==='inspector')setVisited(true);};window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change);},[]);
  useEffect(()=>{
    const names={inspector:'Inspector',privacy:'Draft Privacy Policy',cookies:'Draft Cookie Policy',terms:'Draft Terms',about:'About',contact:'Contact',preferences:'Data preferences',brand:'Logo concepts'};
    document.title=route.page?`${names[route.page]||'Page not found'} · VEYRA AI`:'VEYRA AI — See the detail. Build the vision.';
    if(route.section&&['features','how-it-works','faq'].includes(route.section)){document.getElementById(route.section)?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});}
    else if(lastPage.current!==route.page){main.current?.focus({preventScroll:true});window.scrollTo({top:0,left:0,behavior:"instant"});}
    lastPage.current=route.page;
  },[route]);
  return <div className="site-shell"><a className="skip-link" href="#main" onClick={e=>{e.preventDefault();main.current?.focus();}}>Skip to content</a><header className="site-header"><a className="brand-home" href="#/" aria-label="VEYRA AI home"><Brand/></a><nav aria-label="Main navigation" className={menu?'nav-open':''} id="main-navigation"><a href="#/?section=features">Features</a><a href="#/?section=how-it-works">How it works</a><a href="#/?section=faq">FAQ</a><a href="#/about">About</a></nav><div className="header-actions">{route.page==='inspector'?<button className="quiet tour-replay" onClick={()=>setReplay(n=>n+1)}>Replay tutorial</button>:<span className="review-tag">REVIEW CANDIDATE</span>}<a className="header-launch button-link" href="#/inspector">Open Inspector <Icon name="arrow" size={16}/></a><button className="menu-toggle" aria-label={menu?'Close navigation':'Open navigation'} aria-expanded={menu} aria-controls="main-navigation" onClick={()=>setMenu(v=>!v)}><Icon name={menu?'close':'menu'}/></button></div></header>
    <main id="main" ref={main} tabIndex="-1" className={route.page==='inspector'?'workspace-main':'site-main'}>
      {route.page===''&&<Landing/>}
      {visited&&<InspectorWorkspace active={route.page==='inspector'} replay={replay} preferencesEpoch={preferencesEpoch}/>}
      {route.page==='preferences'&&<DataPreferences onChange={()=>setPreferencesEpoch(n=>n+1)}/>}
      {!['','inspector','preferences'].includes(route.page)&&<InfoPage key={route.page} page={route.page}/>}
    </main><footer className="site-footer"><div><a className="brand-home" href="#/"><Brand compact/></a><p>See the detail. Build the vision.</p></div><div className="footer-links"><a href="#/about">About</a><a href="#/contact">Contact</a><a href="#/privacy">Privacy · draft</a><a href="#/cookies">Cookies · draft</a><a href="#/terms">Terms · draft</a><a href="#/preferences">Data preferences</a><a href="#/brand">Logo concepts</a></div><div className="footer-note"><span>VEYRA AI · V0.4.0 · Code Studio</span><span>Branding, design and policies await owner approval.</span></div></footer>
  </div>;
}
