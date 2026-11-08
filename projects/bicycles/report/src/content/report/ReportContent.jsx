import React from "react";
import { DataComponent, DataTable, EvidenceChart, ReportSection, RichNarrative, SectionNavigator, useDataApp } from "../../data-app-public.jsx";

const number = value => new Intl.NumberFormat("en-CA").format(value);
const compact = value => new Intl.NumberFormat("en-CA", { notation: "compact", maximumFractionDigits: 1 }).format(value);
const pct = value => `${(100 * value).toFixed(1)}%`;
const timeline = rows => rows.map(row=>({...row,referenceYear:String(row.year)}));
const change = (a,b) => `${Math.abs(100*(b/a-1)).toFixed(1)}%`;
const sum = (rows,field) => rows.reduce((total,row)=>total+(row[field]??0),0);
const nav = [{id:"trend",label:"Trend"},{id:"severity",label:"Severity"},{id:"people",label:"Who was harmed"},{id:"vehicles",label:"Other vehicles"},{id:"time",label:"Time"},{id:"conditions",label:"Conditions"},{id:"methods",label:"Methods and evidence"}];

function pooled(rows) {
  const totals = new Map();
  rows.forEach(row=>{
    const value=totals.get(row.category)??{category:row.category};
    ["vehicles","persons","injured","fatalities"].forEach(field=>{if(typeof row[field]==="number") value[field]=(value[field]??0)+row[field];});
    totals.set(row.category,value);
  });
  return [...totals.values()];
}

const shorter = {
  "At an intersection of at least two public roadways":"Public-road intersection",
  "Intersection with parking lot entrance/exit, private driveway or laneway":"Driveway or parking entrance",
  "Overcast, cloudy but no precipitation":"Overcast, no precipitation",
  "Snowing, not including drifting snow":"Snowing",
  "Unknown, other or conflicting vehicle type":"Unknown or conflicting type",
  "Other classified non-bicycle vehicle":"Other classified vehicle",
};

export function ReportContent() {
  const { reviewedRows, visible, appTitle, canEdit, mode, setAppTitle }=useDataApp();
  const get=id=>reviewedRows(id);
  const annual=get("annual_vehicles"), casualties=get("annual_cyclists"), micro=get("micro_annual");
  const quality=get("quality")[0];
  const first=annual[0], last=annual.at(-1), previous=annual.at(-2), pre2020=annual.find(r=>r.year===2019);
  const cf=casualties[0], cl=casualties.at(-1), cp=casualties.at(-2);
  const gender=pooled(get("gender")), age=pooled(get("age_complete"));
  const male=gender.find(r=>r.category==="Male"), unknownAge=age.find(r=>r.category==="Unknown");
  const harm=get("harm"), other=get("other_vehicles");
  const month=pooled(get("month")), warm=month.filter(r=>["May","June","July","August","September"].includes(r.category));
  const road=pooled(get("road_configuration")), intersection=road.find(r=>r.category.startsWith("At an intersection"));
  const darkness=pooled(get("light")).find(r=>r.category==="Darkness");
  const annualSource={annual_vehicles:annual,annual_cyclists:casualties};
  const narrative=(id,queryId,text,extra={})=>visible(id)&&<ReportSection id={id} queryId={queryId} title={id} showHeading={false} {...extra}><RichNarrative id={`${id}:body`} value={text}/></ReportSection>;
  const chart=(id,queryId,title,spec,displayRows,description,height=310)=>visible(id)&&<EvidenceChart id={id} queryId={queryId} title={title} spec={spec} rows={displayRows} sourceRows={get(queryId)} description={description} height={height}/>;
  const table=(id,queryId,title,columns,description)=>visible(id)&&<DataComponent id={id} queryId={queryId} kind="table" title={title} sourceRows={get(queryId)} displayRows={get(queryId)} description={description}><DataTable rows={get(queryId)} columns={columns} searchable={false} compactNumbers={false} caption={title}/></DataComponent>;
  const categoryChart=(queryId,title,measure="vehicles",top=null,height=330)=>{
    let display=pooled(get(queryId));
    if(top) display=display.sort((a,b)=>b[measure]-a[measure]).slice(0,top);
    display=display.map(r=>({...r,label:shorter[r.category]??r.category}));
    return chart(`${queryId}-profile`,queryId,title,{type:"horizontalBar",x:"label",y:measure,valueDecimals:0,stackable:false},display,`Canada, 2010–2023. ${measure==="vehicles"?"Bicycle involvements":"Bicyclists killed"}; unknown categories retained.${top?` Top ${top} categories by count; all categories remain in the source rows.`:""}`,height);
  };
  return <article className="report-content bike-report" aria-label="Canada bicycle collision report">
    <header className="report-hero">
      <h1 data-data-app-title contentEditable={canEdit&&mode==="edit"} suppressContentEditableWarning onBlur={canEdit&&mode==="edit"?event=>setAppTitle(event.currentTarget.textContent.trim()||appTitle):undefined}>{appTitle}</h1>
      <RichNarrative id="report:deck" className="report-deck" value="Canada · National bicycle collision report · 2010–2023"/>
    </header>
    {narrative("executive-summary","annual_vehicles",`## Executive Summary\n\n- **Reported bicycle involvement declined ${change(first.vehicles,last.vehicles)} between 2010 and 2023.** Counts fell from ${compact(first.vehicles)} to ${compact(last.vehicles)}. The 2023 count rose **${change(previous.vehicles,last.vehicles)} from 2022** and was ${change(pre2020.vehicles,last.vehicles)} above 2019. These are bicycles involved in reported casualty collisions; unique collisions are a separate measure.\n- **NCDB Online records ${number(cl.fatalities)} bicyclists killed and ${compact(cl.injured)} injured in 2023.** Across 2010–2023, its direct bicyclist series records ${number(sum(casualties,"fatalities"))} deaths and ${compact(sum(casualties,"injured"))} nonfatal injuries. These counts describe reported harm and do not measure risk per cycling trip.\n- **May through September accounts for ${pct(sum(warm,"vehicles")/sum(month,"vehicles"))} of bicycle involvements.** Public-road intersections account for ${pct(intersection.vehicles/sum(road,"vehicles"))} of involvements. These are descriptive patterns without cycling exposure adjustment.\n\nNational trends and profiles cover **2010–2023**. Linked records support unique collisions, all-road-user harm and co-involved vehicle types for **2010–2021**; those details are unavailable here for 2022–2023.`,{queryIds:["annual_vehicles","annual_cyclists","month","road_configuration"],sourceRowsByQuery:{...annualSource,month:get("month"),road_configuration:get("road_configuration")}})}
    <SectionNavigator sections={nav} placement="auto"/>

    <section id="trend" className="report-section">
      {narrative("trend-text","annual_vehicles",`## 1. Bicycle involvement rebounded in 2023\n\nThe series moves from ${number(first.vehicles)} bicycle involvements in 2010 to ${number(last.vehicles)} in 2023. The largest annual count in this window was ${number(Math.max(...annual.map(r=>r.vehicles)))} in ${annual.reduce((a,b)=>a.vehicles>b.vehicles?a:b).year}. Counts were lower during 2020–2022 before reaching ${number(last.vehicles)} in 2023. The timing of the change does not establish its cause.\n\nA collision involving two bicycles contributes two involvements. **Public linked records identify ${compact(sum(micro,"collisions"))} unique bicycle-involved fatal or injury collisions during 2010–2021**; a corresponding event series for 2022–2023 is not available in these inputs.`,{queryIds:["annual_vehicles","micro_annual"],sourceRowsByQuery:{annual_vehicles:annual,micro_annual:micro}})}
      {chart("involvement-trend","annual_vehicles","Bicycles involved in reported fatal or injury collisions",{type:"line",x:"referenceYear",y:"vehicles",valueDecimals:0,stackable:false},timeline(annual),"Canada, 2010–2023. Vehicle involvements; not unique collisions.")}
      {chart("unique-event-trend","micro_annual","Unique bicycle-involved collisions · linked records, 2010–2021",{type:"line",x:"referenceYear",y:"collisions",valueDecimals:0,stackable:false},timeline(micro),"The record series has a different release vintage from NCDB Online. No 2022–2023 values are estimated.")}
    </section>

    <section id="severity" className="report-section">
      {narrative("severity-text","annual_cyclists",`## 2. Deaths and nonfatal injuries follow different paths\n\nThe direct bicyclist query reports **${number(cl.fatalities)} deaths in 2023**, compared with ${number(cp.fatalities)} in 2022 and ${number(cf.fatalities)} in 2010. Nonfatal injuries increased from ${number(cp.injured)} to ${number(cl.injured)} in 2023 (${change(cp.injured,cl.injured)}), while deaths fell ${change(cp.fatalities,cl.fatalities)}. Annual death counts are small enough that individual-year movements need care.\n\nThe share of bicycle involvements occurring in a fatal collision was **${pct(first.fatal_involvement_share)} in 2010 and ${pct(last.fatal_involvement_share)} in 2023**. A fatal collision means someone died; it does not require the bicyclist to be the person killed. This share is conditional on recorded casualty collisions and is not cycling risk.`,{queryIds:["annual_cyclists","annual_vehicles"],sourceRowsByQuery:annualSource})}
      {chart("casualty-trend","annual_cyclists","Bicyclists killed each year",{type:"line",x:"referenceYear",y:"fatalities",valueDecimals:0,stackable:false},timeline(casualties),"Canada, 2010–2023. Road User Class = Bicyclist; NCDB Online cube dated August 12, 2025.")}
      {chart("injury-trend","annual_cyclists","Bicyclists with reported nonfatal injuries",{type:"line",x:"referenceYear",y:"injured",valueDecimals:0,stackable:false},timeline(casualties),"The reviewed public injury classification does not separate serious from other nonfatal injuries.")}
      {chart("involvement-severity","annual_vehicles","Share of bicycle involvements in fatal collisions",{type:"line",x:"referenceYear",y:"fatalInvolvementShare",valueDecimals:2,stackable:false},timeline(annual).map(r=>({...r,fatalInvolvementShare:r.fatal_involvement_share})),"Fatal-collision bicycle involvements / all casualty-collision bicycle involvements; not deaths / cyclists or risk per trip.")}
    </section>

    <section id="people" className="report-section">
      {narrative("people-text","annual_cyclists",`## 3. Who was harmed\n\nThe person profiles retain unknown age and gender. Male bicyclists account for ${pct(male.fatalities/sum(casualties,"fatalities"))} of recorded bicyclist deaths across 2010–2023. This is a composition share: without cycling exposure by demographic group, it cannot establish who has the highest risk per trip. Unknown age accounts for ${pct(unknownAge.injured/sum(casualties,"injured"))} of reported bicyclist injuries, so age comparisons must retain that gap. The native age bands have unequal widths, including 0–14 and 80+; these counts are not age-standardized.\n\nThe linked records also show harm to other road users in bicycle-involved events. The table below counts identified people with a resolved outcome during **2010–2021**. It retains separate road-user and injury-outcome conflicts; unresolved records are described in Methods.`,{queryIds:["annual_cyclists","gender","age_complete","harm"],sourceRowsByQuery:{annual_cyclists:casualties,gender:get("gender"),age_complete:get("age_complete"),harm}})}
      {visible("gender-profile")&&<DataComponent id="gender-profile" queryId="gender" kind="table" title="Recorded bicyclist injuries and deaths by gender · 2010–2023" sourceRows={get("gender")} displayRows={gender}><DataTable rows={gender} columns={[{field:"category",label:"Recorded gender"},{field:"injured",label:"Nonfatal injuries"},{field:"fatalities",label:"Deaths"}]} searchable={false} compactNumbers={false}/></DataComponent>}
      {categoryChart("age_complete","Bicyclist deaths by recorded age · 2010–2023","fatalities",null,530)}
      {chart("age-injury-profile","age_complete","Bicyclist nonfatal injuries by recorded age · 2010–2023",{type:"horizontalBar",x:"category",y:"injured",valueDecimals:0,stackable:false},age,"Native age bands have unequal widths. Unknown age remains in the population; these are counts, not age-standardized or exposure-adjusted rates.",530)}
      {table("harm-table","harm","People harmed in bicycle-involved events · linked records, 2010–2021",[{field:"road_user",label:"Road user"},{field:"deaths_resolved",label:"Resolved deaths"},{field:"injuries_resolved",label:"Resolved nonfatal injuries"},{field:"unresolved_outcome_people",label:"Unresolved outcomes"}],"Known person identities only; unresolved outcome counts include unknown injury severity or conflicting alternatives, not additional observed casualties.")}
    </section>

    <section id="vehicles" className="report-section">
      {narrative("vehicles-text","other_vehicles",`## 4. Light-duty vehicles are recorded in most bicycle-involved events\n\nA light-duty vehicle was recorded in **${pct(other.find(r=>r.vehicle_group==="Light-duty vehicle").share_of_collisions)}** of the ${compact(sum(micro,"collisions"))} linked bicycle-involved collisions during 2010–2021. That category combines passenger cars, passenger vans, light utility vehicles and light pickups; it cannot isolate SUVs or pickups.\n\nThese are **vehicles recorded in the same event**, not proven striking vehicles. The groups can overlap when an event involves several types. Counts use known vehicle IDs; unknown or conflicting types are retained. This linked comparison does not cover 2022–2023.`)}
      {chart("other-vehicles","other_vehicles","Collisions with another recorded vehicle type · 2010–2021",{type:"horizontalBar",x:"label",y:"collisions",valueDecimals:0,stackable:false},other.map(r=>({...r,label:shorter[r.vehicle_group]??r.vehicle_group})),"Event counts by co-involved vehicle type; overlapping groups, known vehicle IDs only.",400)}
    </section>

    <section id="time" className="report-section">
      {narrative("time-text","month",`## 5. Bicycle involvement is concentrated in the warmer months\n\n**${pct(sum(warm,"vehicles")/sum(month,"vehicles"))} of bicycle involvements occurred from May through September** across 2010–2023. The monthly and time-of-day charts describe reported collision activity; they are not adjusted for the number of people cycling. Unknown month, weekday and hour values remain in their respective totals.`)}
      {chart("month-profile","month","Bicycle involvements by month · 2010–2023",{type:"bar",x:"category",y:"vehicles",valueDecimals:0,stackable:false,colors:["var(--chart-1)"]},month,"Pooled count across all 14 years, including unknown month.")}
      {categoryChart("hour","Bicycle involvements by three-hour period · 2010–2023", "vehicles",null,380)}
      {categoryChart("weekday","Bicycle involvements by weekday · 2010–2023", "vehicles",null,350)}
    </section>

    <section id="conditions" className="report-section">
      {narrative("conditions-text","road_configuration",`## 6. Intersections account for many recorded involvements\n\nPublic-road intersections account for **${pct(intersection.vehicles/sum(road,"vehicles"))}** of bicycle involvements across 2010–2023. Separate categories describe driveway/parking entrances and non-intersection locations. The charts show the most frequent categories, with complete category rows available through source inspection.\n\nDarkness accounts for ${pct(darkness.vehicles/sum(pooled(get("light")),"vehicles"))} of involvements in the vehicle-level query. Weather, lighting and road-surface counts describe conditions at reported events. High counts in clear weather or daylight cannot establish that those conditions are more dangerous; cycling activity is not measured.`,{queryIds:["road_configuration","light"],sourceRowsByQuery:{road_configuration:get("road_configuration"),light:get("light")}})}
      {categoryChart("road_configuration","Most common roadway settings · bicycle involvements, 2010–2023","vehicles",6,350)}
      {categoryChart("weather","Recorded weather · bicycle involvements, 2010–2023","vehicles",6,350)}
      {categoryChart("surface","Recorded road surface · bicycle involvements, 2010–2023","vehicles",6,350)}
      {categoryChart("light","Recorded lighting · bicycle involvements, 2010–2023","vehicles",null,390)}
    </section>

    <section id="methods" className="report-section">
      {narrative("methods-text","source_comparison",`## Methods, coverage and unresolved differences\n\n**Population.** The report concerns the fatal and injury motor-vehicle collision population supplied through public NCDB products. It does not count every bicycle fall, off-road injury or unreported event. E-bikes are not separately identified in the reviewed public schema. National record files used here have no province or location coordinates.\n\n**Two counting grains and coverage periods.** National NCDB Online trends and profiles cover **2010–2023**. Vehicle Type = Bicycle identifies bicycle involvement counts. Road User Class = Bicyclist supplies the primary person casualty series; age and gender profile totals reconcile to it. Linked public records cover **2010–2021** and select events with V_TYPE=17, retaining all linked vehicles and people.\n\n**Identity and missingness.** The linked build retained ${number(quality.input_rows)} source rows and ${number(quality.distinct_rows)} distinct normalized rows. Events use source/year/case keys, vehicles add a valid vehicle ID, and people add a valid person ID. ${number(quality.person_road_user_conflicts)} identified person keys have conflicting road-user codes, ${number(quality.person_severity_conflicts)} have conflicting injury outcomes, and ${number(quality.bicycle_role_disagreements)} has disagreeing bicycle/road-user signals. The ${number(quality.unresolved_rows)} distinct unresolved or dummy rows include ${number(quality.unresolved_positive_casualty_rows)} positive casualty row. Unknown identities are not given invented person IDs, and conflicting outcomes are not silently resolved. Resolved-person totals are not asserted to be complete population counts.\n\n**Release and query differences.** Public records and the online cube disagree in several years. In addition, the vehicle-level online query gives fewer casualties than its person-level query for 2020–2022. In 2020, the queries report 50 versus 54 deaths; in 2021, 39 versus 42; in 2022, 48 versus 51. Both series are preserved. The newer 2024 national publication lists revised bicyclist deaths of 53, 42, 51 and 46 for 2020–2023: it agrees with the online person series for 2021–2023 and differs by one death for 2020. No explanation for the remaining source differences has been established, and no value is replaced to force agreement. Conditions and timing use the vehicle series; casualty trends and demographic totals use the person series.\n\n**Acquisition.** The live tables display an **August 12, 2025** source vintage. Their visible cell matrices were captured and normalized on October 17, 2026. The native CSV download timed out, so these are archived browser table captures rather than native CSV exports. Every category partition and its corresponding annual total was checked for all 14 years. Record input files are independently preserved with pinned hashes.\n\n**Interpretation.** All findings are descriptive. There is no exposure adjustment, causal model, policy-effect estimate or estimate for missing 2022–2023 event records. Source details and numerical rows are inspectable from each component.`,{queryIds:["source_comparison","query_context","published_comparison","quality"],sourceRowsByQuery:{source_comparison:get("source_comparison"),query_context:get("query_context"),published_comparison:get("published_comparison"),quality:get("quality")}})}
      {table("annual-person-table","annual_cyclists","Annual bicyclist casualties · NCDB Online",[{field:"year",label:"Year"},{field:"injured",label:"Nonfatal injuries"},{field:"fatalities",label:"Deaths"}],"Direct Road User Class = Bicyclist series, 2010–2023; source vintage August 12, 2025.")}
      {table("context-table","query_context","Person and vehicle query casualty totals",[{field:"year",label:"Year"},{field:"person_query_fatalities",label:"Bicyclist-query deaths"},{field:"vehicle_query_fatalities",label:"Bicycle-query deaths"},{field:"injury_difference",label:"Person minus vehicle injuries"}],"These query contexts are retained independently; see the source for both complete series.")}
      {table("published-comparison-table","published_comparison","Revised published bicyclist deaths versus the online cube",[{field:"year",label:"Year"},{field:"published_fatalities",label:"2024 publication (revised)"},{field:"online_fatalities",label:"Online person query"}],"2020–2023 subset of the newer official national publication; no 2024 observation is added to this report.")}
      {table("source-comparison-table","source_comparison","Linked-record and online release comparison · 2010–2021",[{field:"year",label:"Year"},{field:"record_bicycle_vehicles",label:"Record bicycle vehicles"},{field:"online_bicycle_vehicles",label:"Online bicycle vehicles"},{field:"record_resolved_bicyclist_deaths",label:"Resolved record bicyclist deaths"},{field:"online_bicyclist_deaths",label:"Online bicyclist deaths"}],"Different source vintages and record-resolution rules; unresolved differences are not corrected by substitution.")}
      <RichNarrative id="report:official-links" value="Official references: [NCDB Online](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en), [NCDB tutorial](https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-1-23-101), [public record catalogue](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a) and [Transport Canada statistics index](https://tc.canada.ca/en/road-transportation/statistics-data)." sourcePreviews={{"https://wwwapps2.tc.gc.ca/Saf-Sec-Sur/7/NCDB-BNDC/p.aspx?l=en&c=100-4-0-1-23-101":{title:"NCDB Online tutorial",summary:"Explains the four-step table builder and that casualties under a vehicle-type selection belong to that selected vehicle type.",source:"Transport Canada",approvedForReport:true}}}/>
    </section>
  </article>;
}
