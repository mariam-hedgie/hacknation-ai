import { useEffect, useMemo, useState } from "react";
import { api, type JourneyResult, type PlanOption, type PlanRequestBody, type PublicSourceCandidate } from "../api";

function distanceFrom(travel: string): number | null {
  const match = travel.match(/([\d.]+)\s*km/i);
  return match ? Number(match[1]) : null;
}

export function JourneyPanel({ option, request }: { option: PlanOption; request: PlanRequestBody }) {
  const travelText = option.travel;
  const modes = useMemo(() => request.travel_modes?.length ? request.travel_modes : ["bus", "train", "car"], [request.travel_modes]);
  const distanceKm = option.distance_km ?? distanceFrom(travelText);
  const [mode, setMode] = useState(
    option.recommended_mode && modes.includes(option.recommended_mode)
      ? option.recommended_mode
      : modes.find((item) => item !== "ambulance") || modes[0],
  );
  const [journey, setJourney] = useState<JourneyResult | null>(null);
  const [journeyError, setJourneyError] = useState("");
  const [sources, setSources] = useState<PublicSourceCandidate[] | null>(null);
  const [sourceMessage, setSourceMessage] = useState("");
  const [loadingSources, setLoadingSources] = useState(false);

  useEffect(() => {
    setJourney(null);
    setJourneyError("");
    api.journey(request.location || "Starting location", option.facility, mode, distanceKm)
      .then(setJourney)
      .catch(() => setJourneyError("A route link could not be prepared. Check the hospital branch before travelling."));
  }, [distanceKm, mode, option.facility, request.location]);

  const checkSources = async () => {
    setLoadingSources(true);
    setSourceMessage("");
    try {
      const response = await api.publicSources(option.facility, request.capability || request.care_task);
      setSources(response.candidates);
      if (!response.candidates.length) setSourceMessage("No public source candidates were found. Call the hospital directly.");
    } catch {
      setSources([]);
      setSourceMessage("Public-source lookup is not configured right now. Use the hospital’s official website or phone number.");
    } finally {
      setLoadingSources(false);
    }
  };

  const ambulanceSelected = modes.includes("ambulance");

  return (
    <div className="journey-panel">
      <div className="section-title">Plan the journey</div>
      <p className="hint">Choose a mode, open the route, then verify the correct branch, schedule, availability, and price.</p>
      {option.recommended_mode && <p className="decision-strip"><strong>Route decision:</strong> {option.recommended_mode} · {option.arrival_feasible === false ? "may miss your arrival date" : "can plausibly meet your arrival date"}</p>}
      <div className="radio-row" aria-label="Travel mode">
        {modes.map((item) => (
          <button type="button" key={item} className={`radio-pill ${mode === item ? "selected" : ""}`} onClick={() => setMode(item)}>
            {item}
          </button>
        ))}
      </div>
      {journeyError && <div className="alert alert-warning">{journeyError}</div>}
      {journey && (
        <>
          <a className="btn btn-primary" href={journey.maps_url} target="_blank" rel="noreferrer">
            Open route in Google Maps
          </a>
          <p className="hint">Google Maps opens externally. Confirm the hospital address and branch before leaving.</p>
          {journey.estimate && (
            <div className="estimate-strip">
              <strong>Seeded comparison:</strong> about {journey.estimate.duration_minutes} minutes · ₹{journey.estimate.cost_low_rupees}–₹{journey.estimate.cost_high_rupees}
              <span>{journey.estimate.disclaimer}</span>
            </div>
          )}
          {mode === "plane" && <p className="hint">Flight schedules and prices must be checked on the provider site. aven does not book or process payment.</p>}
          {journey.ticket_links.length > 0 && (
            <div className="ticket-links">
              {journey.ticket_links.map((link) => <a key={link.url} className="btn" href={link.url} target="_blank" rel="noreferrer">Check {link.label}</a>)}
            </div>
          )}
        </>
      )}

      <details className="disclosure">
        <summary>Need contact, doctor, fee, or ambulance information?</summary>
        <p className="hint">Search only public sources. Results are candidates to verify, not confirmed evidence and do not change the ranking.</p>
        <button className="btn" onClick={checkSources} disabled={loadingSources}>{loadingSources ? "Checking…" : "Check public contact sources"}</button>
        {sourceMessage && <div className="alert alert-info">{sourceMessage}</div>}
        {sources?.map((source) => (
          <div className="source-row" key={source.url}>
            <a href={source.url} target="_blank" rel="noreferrer"><strong>{source.title}</strong></a>
            <p className="hint">{source.snippet || "Open and verify the relevant details on this page."}</p>
            {source.phone_numbers.map((phone) => <a key={phone} className="btn" href={`tel:${phone.replace(/[^+\d]/g, "")}`}>Call {phone}</a>)}
          </div>
        ))}
        {ambulanceSelected && <div className="alert alert-warning">Ambulance was selected, but service is not assumed. Call the hospital to verify pickup time, availability, and any charge. No ambulance is dispatched by aven.</div>}
        <a className="btn emergency-link" href="tel:112">Call 112 for an emergency</a>
      </details>
    </div>
  );
}
