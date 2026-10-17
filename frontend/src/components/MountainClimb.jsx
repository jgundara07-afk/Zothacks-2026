import React from 'react';
import {ArrowRight,Flag} from 'lucide-react';

// Your route up the peak, seen from above as a topographic map. Contours are generated artwork (see README).
const ROUTE=[[30,186],[52,170],[74,158],[92,140],[104,120],[118,100],[130,80],[140,62],[148,44]];
const SEGMENTS=ROUTE.slice(1).map((p,i)=>Math.hypot(p[0]-ROUTE[i][0],p[1]-ROUTE[i][1]));
const LENGTH=SEGMENTS.reduce((a,b)=>a+b,0);
const ROUTE_PATH='M'+ROUTE.map(p=>p.join(' ')).join(' L');

// The point a fraction f (0–1) of the way along the route.
function pointAt(f){
 let left=f*LENGTH;
 for(let i=0;i<SEGMENTS.length;i++){
  if(left<=SEGMENTS[i]){const t=SEGMENTS[i]?left/SEGMENTS[i]:0;return [ROUTE[i][0]+(ROUTE[i+1][0]-ROUTE[i][0])*t,ROUTE[i][1]+(ROUTE[i+1][1]-ROUTE[i][1])*t]}
  left-=SEGMENTS[i];
 }
 return ROUTE[ROUTE.length-1];
}

// The climber moves from the trailhead toward the summit as points go from 0 to 500.
export default function MountainClimb({progress,onSeeProgress}){
 const climb=Math.min(1,progress.points/500);
 const [x,y]=pointAt(climb);
 return <section className="climb"><div className="section-heading"><h2>Your little climb</h2><Flag size={16}/></div><p>One step closer is still closer.</p>
  <svg className="mountain" viewBox="0 0 260 190" role="img" aria-label={`${progress.points} points earned on your mountain climb`}>
   <g className="contours">
   <path d="M260.0 38.2 L249.0 54.0 L246.3 60.0 L245.1 82.0 L243.5 88.0 L223.7 110.0 L215.4 134.0 L208.6 140.0 L190.2 150.0 L181.7 156.0 L177.2 162.0 L172.0 173.9 L168.0 177.9 L158.0 181.7 L150.0 181.2 L142.0 176.2 L132.0 164.9 L126.0 162.8 L116.0 164.6 L84.0 174.2 L72.0 175.3 L66.0 172.9 L46.0 158.9 L20.0 150.5 L14.0 147.3 L7.4 140.0 L4.4 130.0 L5.1 124.0 L10.4 110.0 L11.9 102.0 L11.2 92.0 L7.2 76.0 L7.1 70.0 L9.1 66.0 L21.7 52.0 L24.5 44.0 L23.1 36.0 L13.2 24.0 L12.5 18.0 L16.0 14.8 L20.0 13.5 L36.0 12.6 L46.0 10.1 L53.2 6.0 L58.0 0.0" className="contour major"/>
   <path d="M222.4 0.0 L228.0 8.4 L245.3 24.0 L247.4 28.0 L247.9 34.0 L237.3 56.0 L236.1 76.0 L234.2 84.0 L230.6 90.0 L214.6 108.0 L207.1 126.0 L204.0 130.8 L192.0 139.5 L174.0 145.2 L164.0 144.8 L144.0 138.2 L130.0 139.0 L120.1 144.0 L109.5 154.0 L102.0 159.0 L92.0 163.0 L82.0 164.5 L70.0 162.1 L50.0 151.6 L25.0 142.0 L18.0 136.0 L15.4 128.0 L19.0 106.0 L17.5 82.0 L19.5 72.0 L34.0 50.0 L41.7 28.0 L46.0 23.4 L63.5 10.0 L70.1 0.0" className="contour"/>
   <path d="M214.0 0.0 L231.6 30.0 L231.7 36.0 L227.1 52.0 L227.6 76.0 L223.7 86.0 L205.7 106.0 L195.3 126.0 L187.2 132.0 L176.0 134.7 L146.0 129.6 L126.0 131.3 L112.0 136.8 L94.0 151.3 L88.0 153.7 L82.0 154.4 L70.0 151.5 L38.0 137.7 L29.6 132.0 L26.2 124.0 L24.0 88.0 L24.5 80.0 L26.4 74.0 L40.9 52.0 L48.9 34.0 L55.3 26.0 L72.0 11.3 L78.5 0.0" className="contour"/>
   <path d="M207.1 0.0 L217.0 26.0 L215.3 48.0 L218.9 68.0 L218.7 76.0 L214.0 85.5 L196.1 102.0 L185.4 118.0 L180.0 122.0 L174.0 123.4 L146.0 122.2 L124.0 124.8 L103.7 130.0 L86.0 137.2 L78.0 138.2 L52.0 131.4 L44.5 128.0 L40.0 124.4 L36.0 118.1 L33.3 110.0 L30.3 96.0 L29.7 86.0 L32.9 74.0 L46.9 54.0 L56.1 36.0 L62.8 28.0 L78.2 14.0 L82.6 8.0 L86.0 0.0" className="contour major"/>
   <path d="M200.6 0.0 L205.5 12.0 L207.7 22.0 L205.2 48.0 L209.2 70.0 L207.7 78.0 L200.7 86.0 L166.5 108.0 L150.0 113.6 L122.0 118.7 L96.0 121.6 L72.0 121.9 L56.0 119.8 L46.0 114.5 L39.7 106.0 L35.4 92.0 L36.5 80.0 L40.6 72.0 L52.9 56.0 L64.0 36.4 L86.0 15.1 L90.4 8.0 L93.4 0.0" className="contour"/>
   <path d="M193.9 0.0 L199.3 12.0 L200.8 22.0 L197.1 46.0 L198.6 70.0 L196.2 76.0 L192.0 80.4 L148.0 104.4 L130.0 110.4 L106.0 112.7 L68.0 112.2 L56.0 109.9 L48.0 104.7 L43.4 98.0 L41.2 88.0 L42.7 80.0 L47.6 72.0 L61.3 56.0 L72.0 37.8 L94.9 16.0 L101.5 0.0" className="contour"/>
   <path d="M186.4 0.0 L192.5 10.0 L194.3 22.0 L190.3 44.0 L189.5 66.0 L186.9 72.0 L182.0 77.1 L172.0 83.1 L144.0 96.1 L126.7 102.0 L116.0 102.8 L96.0 101.0 L68.0 103.6 L56.0 100.4 L52.0 97.1 L49.1 92.0 L48.5 86.0 L50.4 80.0 L56.0 72.9 L71.8 60.0 L79.5 44.0 L83.9 38.0 L104.0 20.0 L107.3 14.0 L111.6 0.0" className="contour major"/>
   <path d="M176.4 0.0 L184.6 8.0 L187.8 18.0 L182.6 60.0 L180.8 66.0 L176.0 72.3 L166.0 78.9 L148.0 85.8 L134.0 88.5 L126.0 87.3 L120.0 83.2 L100.8 54.0 L98.5 48.0 L98.9 44.0 L100.9 40.0 L117.0 22.0 L123.2 6.0 L127.7 0.0" className="contour"/>
   <path d="M68.0 90.4 L64.8 90.0 L62.5 88.0 L63.0 84.0 L66.0 82.0 L70.0 82.3 L72.6 86.0 L72.0 88.2 L68.0 90.4 Z" className="contour"/>
   <path d="M150.0 78.2 L136.0 78.6 L126.0 73.1 L120.3 66.0 L116.0 58.0 L114.2 52.0 L114.3 46.0 L117.0 40.0 L128.0 26.0 L139.5 8.0 L150.0 3.2 L164.0 3.0 L174.0 7.0 L178.0 11.2 L180.1 16.0 L180.5 24.0 L176.3 56.0 L173.5 64.0 L168.3 70.0 L160.0 74.9 L150.0 78.2 Z" className="contour"/>
   <path d="M154.0 70.3 L144.0 71.6 L134.0 68.3 L126.8 60.0 L124.8 50.0 L129.1 40.0 L148.0 18.0 L154.0 13.8 L162.0 12.8 L168.0 15.7 L170.9 22.0 L169.6 52.0 L168.0 58.3 L164.4 64.0 L154.0 70.3 Z" className="contour major"/>
   <path d="M150.0 62.4 L144.0 62.3 L139.6 60.0 L136.8 56.0 L136.3 50.0 L139.6 44.0 L144.0 40.0 L150.0 37.0 L154.0 36.8 L156.4 38.0 L159.1 42.0 L160.2 52.0 L157.4 58.0 L150.0 62.4 Z" className="contour"/>   </g>
   <path d={ROUTE_PATH} className="route-ahead"/>
   <path d={ROUTE_PATH} className="route-done" pathLength="1" strokeDasharray={`${climb} 1`}/>
   <path d="M148 44 V20 L164 25 L148 30" className="summit-flag"/>
   <text x="156" y="48" className="map-label">PEAK · 500</text>
   <text x="8" y="182" className="map-label">TRAILHEAD</text>
   <circle className="climber-halo" cx={x} cy={y} r="11"/>
   <circle className="climber" cx={x} cy={y} r="5"/>
  </svg>
  <div className="climb-stats"><strong>{progress.points}<small> points</small></strong><span>Trail {Math.floor(progress.points/100)+1}</span></div>
  <div className="progress-track"><span style={{width:`${progress.points%100}%`}}/></div>
  <small>{100-progress.points%100} points to your next milestone</small>
  <button className="text-link" onClick={onSeeProgress}>See your progress <ArrowRight size={15}/></button>
 </section>
}
