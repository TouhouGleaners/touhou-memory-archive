import{s as m}from"./index-BYxpIWNi.js";import{s as S}from"./index-_TQn5Ggz.js";import{s as x}from"./index-N9qesT-p.js";import{G as b,c,o as i,H as f,a as e,z as w,r as $,q as B,x as P,u as k,B as t,k as o,j as g,m as l,t as d,_ as D}from"./index-CzS_kdjK.js";import{u as V,i as H}from"./useVideos-CqilWS6k.js";import"./index-DMwSFFWj.js";import"./index-BRpy79cv.js";var N=`
    .p-progressspinner {
        position: relative;
        margin: 0 auto;
        width: 100px;
        height: 100px;
        display: inline-block;
    }

    .p-progressspinner::before {
        content: '';
        display: block;
        padding-top: 100%;
    }

    .p-progressspinner-spin {
        height: 100%;
        transform-origin: center center;
        width: 100%;
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        margin: auto;
        animation: p-progressspinner-rotate 2s linear infinite;
    }

    .p-progressspinner-circle {
        stroke-dasharray: 89, 200;
        stroke-dashoffset: 0;
        stroke: dt('progressspinner.colorOne');
        animation:
            p-progressspinner-dash 1.5s ease-in-out infinite,
            p-progressspinner-color 6s ease-in-out infinite;
        stroke-linecap: round;
    }

    @keyframes p-progressspinner-rotate {
        100% {
            transform: rotate(360deg);
        }
    }
    @keyframes p-progressspinner-dash {
        0% {
            stroke-dasharray: 1, 200;
            stroke-dashoffset: 0;
        }
        50% {
            stroke-dasharray: 89, 200;
            stroke-dashoffset: -35px;
        }
        100% {
            stroke-dasharray: 89, 200;
            stroke-dashoffset: -124px;
        }
    }
    @keyframes p-progressspinner-color {
        100%,
        0% {
            stroke: dt('progressspinner.color.one');
        }
        40% {
            stroke: dt('progressspinner.color.two');
        }
        66% {
            stroke: dt('progressspinner.color.three');
        }
        80%,
        90% {
            stroke: dt('progressspinner.color.four');
        }
    }
`,z={root:"p-progressspinner",spin:"p-progressspinner-spin",circle:"p-progressspinner-circle"},C=b.extend({name:"progressspinner",style:N,classes:z}),E={name:"BaseProgressSpinner",extends:x,props:{strokeWidth:{type:String,default:"2"},fill:{type:String,default:"none"},animationDuration:{type:String,default:"2s"}},style:C,provide:function(){return{$pcProgressSpinner:this,$parentInstance:this}}},y={name:"ProgressSpinner",extends:E,inheritAttrs:!1,computed:{svgStyle:function(){return{"animation-duration":this.animationDuration}}}},I=["fill","stroke-width"];function M(s,a,h,u,v,n){return i(),c("div",f({class:s.cx("root"),role:"progressbar"},s.ptmi("root")),[(i(),c("svg",f({class:s.cx("spin"),viewBox:"25 25 50 50",style:n.svgStyle},s.ptm("spin")),[e("circle",f({class:s.cx("circle"),cx:"50",cy:"50",r:"20",fill:s.fill,"stroke-width":s.strokeWidth,strokeMiterlimit:"10"},s.ptm("circle")),null,16,I)],16))],16)}y.render=M;const T={class:"dashboard-home"},W={key:2,class:"cards"},j={class:"card-value"},q={class:"card-value"},A={class:"card-value"},G=w({__name:"DashboardHome",setup(s){const{videos:a,loading:h,loadError:u,loadVideos:v}=V(),n=$({total:0,touhou:0,uploaders:0});function _(){n.value.total=a.value.length,n.value.touhou=a.value.filter(p=>H(p.touhou_status)).length,n.value.uploaders=new Set(a.value.map(p=>p.uploader_name)).size}return B(a,_,{immediate:!0}),P(v),(p,r)=>(i(),c("div",T,[r[3]||(r[3]=e("h3",null,"仪表盘",-1)),t(u)?(i(),k(t(S),{key:0,severity:"error",closable:!1},{default:o(()=>[l(d(t(u)),1)]),_:1})):t(h)?(i(),k(t(y),{key:1,style:{width:"50px",height:"50px"}})):(i(),c("div",W,[g(t(m),null,{title:o(()=>[...r[0]||(r[0]=[e("div",{class:"card-title"},[e("i",{class:"pi pi-video"}),l(" 视频总数")],-1)])]),content:o(()=>[e("div",j,d(n.value.total),1)]),_:1}),g(t(m),null,{title:o(()=>[...r[1]||(r[1]=[e("div",{class:"card-title"},[e("i",{class:"pi pi-star"}),l(" 东方视频")],-1)])]),content:o(()=>[e("div",q,d(n.value.touhou),1)]),_:1}),g(t(m),null,{title:o(()=>[...r[2]||(r[2]=[e("div",{class:"card-title"},[e("i",{class:"pi pi-users"}),l(" UP主数量")],-1)])]),content:o(()=>[e("div",A,d(n.value.uploaders),1)]),_:1})]))]))}}),R=D(G,[["__scopeId","data-v-d5fac7da"]]);export{R as default};
