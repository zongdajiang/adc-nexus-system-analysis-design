// A tiny timer controller with an injected clock for deterministic regression tests.
export function createCarousel({count,onChange,onState,interval=5500,clock=globalThis}) {
  let index=0,paused=false,hidden=false,reduced=false,disposed=false,timer=null;
  const stop=()=>{if(timer!==null)clock.clearInterval(timer);timer=null;};
  const restart=()=>{stop();if(!paused&&!hidden&&!reduced&&!disposed)timer=clock.setInterval(()=>{index=(index+1)%count;onChange(index);},interval);onState?.({paused,hidden,reduced,running:timer!==null});};
  return {
    start:restart,
    move(n){if(disposed)return;index=((n%count)+count)%count;onChange(index);restart();},
    pause(value){if(disposed)return;paused=value;restart();},
    visibility(value){if(disposed)return;hidden=value;restart();},
    reduced(value){if(disposed)return;reduced=value;restart();},
    dispose(){disposed=true;stop();},
  };
}
