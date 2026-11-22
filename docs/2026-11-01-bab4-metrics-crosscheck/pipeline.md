# Crosscheck of MQTT pipeline metrics and measurement methods against standards and literature

Research date: 1 Nov 2026. All source files are in
`/home/mrrizaldi/dev/projek-akhir/laporan/pustaka/belum-dirujuk/riset-pengukuran/pipeline/`
(abbreviated `P/`). The `.txt` files from MDPI are the HTML text of the article because the MDPI PDF
download was refused by the server (403); they contain the full text, but without page numbers, so
the references cite subsection and table numbers.

Besides the literature, the measurement tool code was read directly: `dashboard/ukur_pipeline.py` (lines 61–128)
and `laporan/buku-pa/bab/bab3.tex` (tab:pengujian-pipeline), `bab4.tex` (sec pipeline).
Findings from the code are marked **[kode]**.

---

## 1. Crosscheck table

| # | Our metric / measurement method | Standard practice / literature (source + location) | Status | Concrete suggestion |
|---|---|---|---|---|
| 1 | **PDSR** = packets with a PUBACK on the first attempt / total PUBLISH, computed on the device, wait limit 5 s | RFC 7680 §2.4 (p. 7) defines one-way loss with a threshold Tmax; §2.8.2 (p. 11): Tmax "MUST be reported". Because our success is determined by the return of the PUBACK, the more accurate definition is the **round-trip loss** of RFC 6673 §4.3 (p. 7): Loss = 0 if Src receives the reply packet before TstampSrc + Tmax. Kim 2026 Table 8 and Table 10 compute "message success rate" as messages received by the subscriber / messages sent; Lima 2025 §III-A (p. 4) computes loss as the difference between the number of publishes and the number that arrived at the subscriber; Escobedo 2026 §3.2 (pp. 11–12) detects loss with sequence numbers at the receiver. | **Different but defensible** | State in Chapter 3/4 that PDSR is the first-attempt *round-trip* success (equivalent to 1 − the RFC 6673 round-trip loss ratio) with Tmax = 5 s, Type-P = MQTT 3.1.1 PUBLISH QoS 1 over TCP, payload size of the batch. Separate it clearly from the "application delivery ratio" (beats arriving at ThingsBoard / beats produced), which the literature calls PDR/message success rate and which we reach at 100%. |
| 2 | PDSR target ≥ 95%, results 292/292, 253/255, 188/188 | Y.1541 §5.3.2 (p. 11): the observed value must be recorded "along with any assumptions and confidence intervals". RFC 6703 §8.2 (p. 24): the sample size (number of packets) must be reported. No standard gives a minimum number of packets for PDR. | **Lacking, needs addition** (easy) | Add the exact binomial confidence interval (Clopper–Pearson, 95%, two-sided), computed from the book's figures: repetition 1: 98.74–100%; repetition 2: 97.20–99.90%; repetition 3: 98.06–100%; pooled 733/735 = 99.73% with CI 99.02–99.97%. The lower bound of every repetition is above 95%, so the claim "PDSR ≥ 95%" passes statistically even though the sample is small. Calculation: for 0 failures, the one-sided 95% lower bound = 0.05^(1/n); n ≥ 59 packets is already enough to state > 95%, and n ≥ 299 for > 99%. |
| 3 | **End-to-end latency** = time the PC sees the row in the ThingsBoard REST API − ts of the R-peak event | RFC 7679 §3.4 defines *one-way delay* from the first bit sent to the last bit received (wire time). Our metric is a derived application metric that includes processing on the device. RFC 2330 §6.3 (pp. 7–8): for derived/composed metrics, the propagation of uncertainty must be analysed. Adochiei 2025 §3.4 places timestamps at four points (publisher, broker, InfluxDB write, Grafana ingest) and **excludes the Grafana render time**. Kim 2026 Table 8/10: from "data generation at a sensor node" to "reception at the subscriber", the subscriber timestamp is taken before the database write. Lima 2025 §III-B (p. 5): publish time (user property) to receive time at the subscriber. | **Conforms** in practice (our starting point is stricter: the event, not the publish), but **the definition in the book is inconsistent** (see Gap 1) | Rename the metric to "event-to-API latency" or state its definition explicitly: from the R-peak (ts) until the row is available in the ThingsBoard REST API, **without** the dashboard render time. The decomposition (869 ms device side, broker 1.1 ms) is already in line with the multi-point approach of Adochiei and Reiher 2022. |
| 4 | Clock synchronisation: device SNTP + gettimeofday; the device–PC clock offset is corrected from `epoch_ms` in the serial status line (median of 5 samples, once at the start) | RFC 7679 §3.7.1 (pp. 10–11): total clock uncertainty = Esynch(t) + Rsource + Rdest, and "should be included in the error/uncertainty analysis". §3.8.3 (p. 15): systematic error "SHOULD be removed" and the calibration error e (95%) "SHOULD" be reported. RFC 7680 §2.8.3 (p. 11): the degree of synchronisation "MUST be reported". RFC 7679 §3.5 (p. 8): ordinary NTP is only a few ms. Literature: Adochiei 2025 §3.4.1: local NTP (chrony, 60 s update), drift ±5 ms per 60 s, and admits there is no CI or latency distribution. Kim 2026 Tables 3 and 10: NTP every 30 minutes, uncertainty not reported. Lima 2025 p. 5: the load driver and the subscriber on the same host "to ensure the accuracy of the end-to-end delay". Reiher 2022 p. 5: because NTP clocks are "not guaranteed to be synchronized exactly", they use round-trip latency on a single clock. Silva 2021 §5: publisher (laptop) and subscriber (RPi) on different machines without mentioning synchronisation. | **Different but defensible.** The "measure the clock offset then correct" approach is a form of removing systematic error as in RFC 7679 §3.7.3, and is more explicit than most papers. **Lacking**: the size of the uncertainty is not reported. | Report (a) the spread of the 5 offset samples (min–max) as an estimate of Esynch; (b) also measure the offset at the **end** of the repetition to capture skew (RFC 7679 §3.7.1 skew item); (c) state the resolution: device ts 1 ms, PC side determined by the polling cycle. **[kode]** The PC timestamp for the offset is taken in a loop that sleeps 50 ms (`time.sleep(0.05)`), so the offset can be biased by up to ±50 ms + USB serial latency; the bias direction makes the latency look smaller. Just write it down as an uncertainty component, or reduce the sleep to 1 ms. |
| 5 | REST polling ±100 ms; "lower bound" = time before the request of the poll that first sees the row | RFC 7679 §3.7.1: the destination clock resolution "adds ... uncertainty to any time value measured with it". RFC 6703 §4.1.2 (p. 11) allows an application threshold to be applied in post-processing. | **Lacking, needs addition** (explanation only) | **[kode]** The row actually appears between the previous poll query and the current poll query. The `sebelum` value of the current poll is **not a true lower bound**: it can be larger than the actual appearance time by up to one cycle (100 ms + REST duration). This bias is conservative (it overstates latency), so it is safe for the target claim. Write the term as a "conservative estimate" with an uncertainty of ≈ one polling cycle, not a "lower bound". |
| 6 | Statistics: **median** assessed against the 2,000 ms target, p95 reported (original plan: "mean") | RFC 6703 §3.1 (p. 6): "we recommend providing both the mean delay and the median delay". §5.2 (pp. 15–16): the median is stable against outliers, and "minimum, maximum, and 95th percentile have value", the mean–median comparison is informative. RFC 7679 §5.1–5.3 (pp. 19–20): percentile, median, minimum. Y.1541 Table 1 (p. 9): IPTD as an upper bound on the **mean**. Literature: Kim 2026 Table 11 (mean and maximum), Silva 2021 §5 (AVG, STDEV, MAX, MIN, MED, CI from 10 repetitions), Reiher 2022 §IV-D (p. 6): mean as the main metric + min, max, median, SD, Lima 2025 (boxplot median, table of means), Adochiei 2025 §3.4.2 (averaged). | **Different but defensible** (the median is supported by RFC 6703). **Lacking** because the mean written in the plan is not reported. | Also report **mean ± SD, minimum, maximum** per repetition. The use of the median is justified with RFC 6703 §5.2. With a long tail (p95 3,304 ms), the mean is likely > the median, and the mean must still be ≤ 2,000 ms to stay consistent with the plan. The raw data already exists, it only needs recomputation. **[kode]** p95 is computed as `v[int(0.95*(n-1))]`; RFC 2330 §11.3 (pp. 25–26) defines the percentile as the smallest value x with F(x) ≥ p, that is rank ⌈0.95n⌉. For n = 292 the result is off by one rank (277 vs 278). The difference is small but should be made uniform. |
| 7 | Handling of lost/late packets in the latency statistics | RFC 7679 §5.1 (p. 19): *undefined* (lost) values are treated as infinite in percentiles. RFC 6703 §3.1: mean/median are computed on the conditional distribution (the ones that arrive) with a long wait threshold. | **Conforms** (application data loss = 0, so conditional = unconditional) | Write one sentence: all beats sent appear in ThingsBoard within the measurement window, so there are no *undefined* values. Beats from the 2 resent packets are counted with their full latency, including the 5 s timeout. Make sure this is indeed so in the data. |
| 8 | Latency target **≤ 2 s** | ITU-T G.1010 Figure 2 (p. 6): category **Responsive (delay ~2 s)**, as an error-intolerant category between Interactive (<<1 s) and Timely (~10 s). Table I.2 (p. 9): transaction/web/e-mail access "Preferred < 2 s, Acceptable < 4 s", information loss "Zero". ITU-T H.810 (Continua) §6.1.7.4–6.1.7.5 (pp. 36–37): measured parameters (heart rate, SpO2) = *better.medium*, E2E ~1 s; physiological alarms = *best.high*, E2E ~10 s; values "relative to transport". Skorin-Kapov 2010 Table 1: tele-monitoring "small delay: No"; Table 3: ECG max delay "approx. 1 s", loss "Zero"; Table 4: real-time tele-monitoring "<300 ms E2E one-way for hard real-time ECG (certain applications may tolerate <1 s E2E for ECG)", non-real-time tele-monitoring "N.A.". Zhong 2022 Table 3: ECG "P2PLatency <250 ms", that is the point-to-point WBAN link latency (sensor–hub), **not** E2E to the server. | **Defensible with a note.** 2 s is in line with the G.1010 Responsive category and lies between H.810 *better.medium* (~1 s, per-beat result) and *best.high* (~10 s, alarm). 2 s **exceeds** the Skorin-Kapov figures for real-time ECG (<300 ms / <1 s), but those figures are for an emergency ECG **waveform** stream, whereas we send a **classification label per beat**. | Replace/complete the reference for the latency budget: G.1010 Figure 2 + Table I.2 and H.810 §6.1.7.5 as the main basis, Skorin-Kapov Table 1/4 to show that non-emergency telemonitoring does not demand a small delay. Zhong 2022 (<250 ms P2P) should **not** be used as an E2E comparison because its scope is the BAN link. Option for the p95 target: G.1010 "Acceptable < 4 s" (the worst p95 of 3,304 ms is still below it). This is the user's decision. |
| 9 | Delay variation / jitter: not reported | RFC 3393 §2.4 (p. 6) IPDV; RFC 5481 §7.3 (pp. 29–30): PDV = D(i) − D(min) is preferred for a one-number summary; RFC 6703 §3.1 (p. 6): "pseudo range" = high percentile − minimum. Y.1541 Table 1: IPDV = 1−10⁻³ quantile − minimum. Skorin-Kapov Table 1: tele-monitoring "small jitter: No". | **Different but defensible** (jitter is not critical for telemonitoring) | Optional: report PDV = p95 − min per repetition, the data is already available. Do not use the 99.9% quantile because Y.1541 §5.3.1 (p. 10) states ≥ 1000 packets are needed. |
| 10 | **Sample size**: 3 repetitions × 120–180 s (latency n ±200–290 beats per repetition; 735 packets) | RFC 5481 §8.4 (p. 33): "test using durations that are similar in length to the session time of interest", and the consistency of Internet paths is observed at the scale of minutes. Y.1541 §5.3.2 (pp. 10–11): a 1-minute evaluation interval is suggested, "Any minute observed should meet these objectives", CI recorded. RFC 6703 §8.2 (p. 24): report n; "large" must be explained with its implications. Practice: Adochiei 10 × 60 s; Silva 10 repetitions per scenario; Lima 10 repetitions (±4 hours); Saif 2022 and Reiher 2022 (60 s per experiment); Escobedo ±3 million WiFi packets and a 12-hour LTE-M test. | **Lacking for latency/tail**, **sufficient for PDSR** (see item 2) | (a) Split the existing data into 1-minute intervals (±8 intervals) and report the median and p95 per minute (the Y.1541 way), so no re-measurement is needed. (b) Report a nonparametric percentile CI. Example n = 201: the 95% CI for p95 lies between the 185th and 198th order statistics, almost the range p92–p98.5. This is why p95 "swings". (c) If measurement time is available: add repetitions up to 10 (common practice) or one long 30–60 minute repetition to approach the monitoring session duration (RFC 5481 §8.4). |
| 11 | **Resilience**: broker frozen (`docker pause`) for 24 s, once; data lost 0; flush ≤ 24.6 s; plan: WiFi forcibly cut | Peer-reviewed work that measures controlled outages on a health MQTT pipeline is **rarely found**. da Silva et al. 2027 (LNCS, **abstract only**) tests three states (connected, offline, reconnect + backlog synchronisation) with graded load and measures throughput, E2E latency, resources, and "backlog draining time". Escobedo 2026 §3.2 (p. 12): loss rises when cellular signal strength fluctuates; §4 (p. 15): local buffering is only a future work plan. H.810 §3.2.62: definition of *store and forward*. Saif 2022 §VII (pp. 4–5) uses NetEm for delay, rate, and uniform drop 0–6%, but not an outage. Docker documentation (`docker container pause`): uses the cgroup freezer, "the process is unaware ... that it is being suspended". | **Lacking, needs addition** | `docker pause` freezes only the broker **process**, while the WiFi radio, AP association, and TCP in the host kernel stay alive. **A technical inference not yet verified with a packet capture**: the host kernel probably still ACKs TCP segments as long as the receive buffer suffices, so what is tested is the **application PUBACK timeout** path, not the **link loss** path (WiFi disconnect event, re-association, DHCP, new TCP, MQTT CONNECT). The two are not equivalent. Suggestion: (1) add a real WiFi disconnect test (AP switched off/unplugged) as in the Chapter 3 plan, ≥ 3 repetitions, with graded durations (e.g. 30 s, 5 minutes, 30 minutes); (2) metrics: data lost (beats produced vs arrived, ideally via beat sequence numbers), reconnect time, drain time, drain rate (beats/s), and the latency of beats from the backlog; (3) if there is no time, write in the limitations that what was tested is a broker failure, not a link failure. |
| 12 | **Duplicates**: 0 duplicate ts in ThingsBoard (upsert per ts) | RFC 7680 §2.5 (p. 8): a duplicated packet is counted as "received". Lima 2025 p. 5: the message ID is used at the subscriber to count duplicates at QoS 1. | **Lacking (the logic is circular)** | Because ThingsBoard overwrites per ts, the count of "duplicate ts in ThingsBoard" is **always 0 by construction**, so it does not prove whether duplicates were sent. What can be proven: deduplication works **if** duplicates occur. Suggestion: count duplicates on the sender/broker side (number of resent PUBLISH = 2 in repetition 2) or with an independent subscriber (`mosquitto_sub`) that records the ts, then show that beats from the resent packets are still recorded once in ThingsBoard. |
| 13 | Data lost = unique REST rows vs the number "sent" by the device (267/267) | Escobedo 2026 §2 and §3.2: per-packet sequence number at the receiver. RFC 7680 §2.4: loss is determined at Dst against what Src sent. | **Different but defensible** | The comparison should ideally be the beats **produced** by the detector, not those "sent" (the sent counter does not see beats lost before entering the queue). Deterministic replay makes the expected number of beats computable, so write down the comparison. |
| 14 | Context: unisolated home WiFi, RSSI −50 dBm, replay signal ±1.6 beats/s | RFC 7679 §3.8 (pp. 14–15): calibration and context "MUST be carefully considered and SHOULD always be reported", including Type-P and path. Y.1541 §5.3.3: packet size is recorded. | **Conforms** | Add the packet payload size (bytes per batch), MQTT version, WiFi channel, and the number of surrounding APs if available. This is enough for the defence. |

---

## 2. Source list

Status: **TL** = full text read (the method/table parts that are quoted), **ABS** = abstract only,
**JDL** = title/metadata only.

### Standards

| Proposed key | Title | Authors | Year | Venue | DOI | Status | File |
|---|---|---|---|---|---|---|---|
| ietf_rfc7679 | A One-Way Delay Metric for IP Performance Metrics (IPPM) | Almes, Kalidindi, Zekauskas, Morton | 2016 | IETF RFC 7679 (STD 81) | 10.17487/RFC7679 | TL | `P/rfc7679.txt` |
| ietf_rfc7680 | A One-Way Loss Metric for IP Performance Metrics (IPPM) | Almes, Kalidindi, Zekauskas, Morton | 2016 | IETF RFC 7680 (STD 82) | 10.17487/RFC7680 | TL | `P/rfc7680.txt` |
| ietf_rfc2330 | Framework for IP Performance Metrics | Paxson, Almes, Mahdavi, Mathis | 1998 | IETF RFC 2330 | 10.17487/RFC2330 | TL (§6.3, §10.1, §11.3) | `P/rfc2330.txt` |
| ietf_rfc6703 | Reporting IP Network Performance Metrics: Different Points of View | Morton, Ramachandran, Maguluri | 2012 | IETF RFC 6703 | 10.17487/RFC6703 | TL | `P/rfc6703.txt` |
| ietf_rfc5481 | Packet Delay Variation Applicability Statement | Morton, Claise | 2009 | IETF RFC 5481 | 10.17487/RFC5481 | TL (§6.5, §7.3, §8.4) | `P/rfc5481.txt` |
| ietf_rfc3393 | IP Packet Delay Variation Metric for IPPM | Demichelis, Chimento | 2002 | IETF RFC 3393 | 10.17487/RFC3393 | TL (§2.4 only) | `P/rfc3393.txt` |
| ietf_rfc6673 | Round-Trip Packet Loss Metrics | Morton | 2012 | IETF RFC 6673 | 10.17487/RFC6673 | TL (§3–5) | `P/rfc6673.txt` |
| itu_g1010 | End-user multimedia QoS categories | ITU-T | 2001 | Rec. ITU-T G.1010 (11/2001) | – | TL | `P/itu_g1010_2001.pdf` |
| itu_y1541 | Network performance objectives for IP-based services | ITU-T | 2011 | Rec. ITU-T Y.1541 (12/2011) | – | TL (§5.3, Tables 1–2) | `P/itu_y1541_2011.pdf` |
| itu_h810 | Interoperability design guidelines for personal connected health systems: Introduction | ITU-T | 2019 | Rec. ITU-T H.810 (11/2019) | – | TL (§3.2, §6.1.7) | `P/itu_h810_2019.pdf` |

Key quotes:

- RFC 7679 §3.7.1, p. 11: "these clock-related problems introduce a total uncertainty of
  Esynch(t)+ Rsource + Rdest. This estimate of total clock-related uncertainty should be included
  in the error/uncertainty analysis of any measurement implementation."
- RFC 7679 §3.8.3, p. 15: "If the systematic error can be determined, it SHOULD be removed from
  the measured values." / "You SHOULD also report the calibration error, e, such that the true
  value is the reported value plus or minus e, with 95% confidence".
- RFC 7679 §3.5, p. 8: "Ordinary application of NTP may allow synchronization to within several
  msec".
- RFC 7679 §5.1, p. 19: "In computing this percentile, undefined values are treated as infinitely
  large."
- RFC 7680 §2.8.2, p. 11: "The threshold, Tmax, between a large finite delay and loss ... MUST be
  reported." §2.8.3: "The degree of synchronization between the Src and Dst clocks MUST be
  reported."
- RFC 7680 §2.5, p. 8: "If the packet is duplicated along the path ... then the packet is counted
  as received."
- RFC 6673 §4.3, p. 7: "Type-P-Round-trip-Loss = 1: ... Src did not receive the last bit of the
  reflected packet before the waiting time lapsed at TstampSrc + Tmax."
- RFC 6703 §3.1, p. 6: "For packet delay, we recommend providing both the mean delay and the
  median delay with lost packets designated as undefined".
- RFC 6703 §5.2, p. 15: "The median is stable in distributions with a few outliers or without
  them." / "additional statistics such as the minimum, maximum, and 95th percentile have value when
  summarizing a distribution."
- RFC 6703 §8.2, p. 24: "Even if only the sample size (in terms of number of packets) is given
  for each value or summary statistic, it imparts a notion of the confidence in the result."
- RFC 2330 §6.3, p. 8: "minimize their uncertainties/errors, understand and document the sources
  of uncertainty/error, and quantify the amounts of uncertainty/error."
- RFC 2330 §11.3, p. 26: "We will use the term "percentile" to refer to the smallest value of x
  for which F(x) >= a given percentage."
- RFC 5481 §8.4, p. 33: "The primary recommendation here is to test using durations that are
  similar in length to the session time of interest."
- G.1010 Figure 2, p. 6: "Interactive (delay <<1 s) | Responsive (delay ~2 s) | Timely
  (delay ~10 s) | Non-critical (delay >>10 s)".
- G.1010 Table I.2, p. 9 (high-priority transaction row): "Preferred < 2 s / Acceptable < 4 s
  ... Zero" (information loss). Table note: "In some cases, it may be more appropriate to consider
  these values as response times."
- Y.1541 Table 1 general note, p. 9: "An evaluation interval of 1 minute is suggested for IPTD,
  IPDV, and IPLR and, in all cases, the interval must be recorded with the observed value."
- Y.1541 §5.3.2, p. 11: "the value used must be recorded with the observed value, along with any
  assumptions and confidence intervals."
- Y.1541 §5.3.1, p. 10: "a sample with 1000 packets is the minimum necessary to evaluate this
  bound" (for the 1−10⁻³ quantile).
- H.810 §6.1.7.4, p. 36: "high latency typically refers to a maximum of 10 seconds, medium latency
  typically refers to a maximum of 1 second ... However, these latencies are transport-dependent".
- H.810 §6.1.7.5, pp. 36–37: "better.medium: ... a measured parameter (blood pressure, blood oxygen
  saturation (SpO2), heart rate, etc.) – overall end-to-end latency = ~1 s" and "best.high: ... both
  physiological driven alarms and equipment issued alarms – overall end-to-end latency = ~10 s".
- H.810 §3.2.62: "store and forward: This is a technique that is often used by a device when the
  connection to a partner may be intermittent."

### Healthcare QoS requirement papers

| Key | Title | Authors | Year | Venue | DOI | Status | File |
|---|---|---|---|---|---|---|---|
| skorinkapov_2010 (already in bib) | Analysis of QoS Requirements for e-Health Services and Mapping to Evolved Packet System QoS Classes | Skorin-Kapov, Matijasevic | 2010 | Int. J. Telemedicine and Applications | 10.1155/2010/628086 | TL (PMC2952804) | `P/skorinkapov_2010.txt` |
| zhong_2022 (already in bib) | Technological Requirements and Challenges in Wireless Body Area Networks for Health Monitoring: A Comprehensive Survey | Zhong et al. | 2022 | Sensors 22(9):3539 | 10.3390/s22093539 | TL (PMC9105253) | `P/zhong_2022.txt` |

- Skorin-Kapov Table 1: "Tele-monitoring | Low | No | No | Yes" (columns throughput, small delay,
  small jitter, sensitivity to context).
- Skorin-Kapov Table 3: "Electrocardiogram (ECG) | 1–20 kbps | approx. 1 s | Zero".
- Skorin-Kapov Table 4: "Real-time tele-monitoring ... <300 ms E2E one-way for hard real-time ECG
  (certain applications may tolerate <1 s E2E for ECG) | Zero" and "Non-real-time tele-monitoring
  ... Not Available (N.A.) | Zero".
- Zhong Table 3: "ECG | 72 kb/s | <6 | Star | <3 s | <250 ms | <10–10 | <10% | >1 week" (columns
  Setup Time, P2PLatency, BER). These are the technical needs of a BAN application, not E2E to the server.

### MQTT / healthcare IoT benchmark papers

| Key | Title | Authors | Year | Venue | DOI | Scopus ID | Status | File |
|---|---|---|---|---|---|---|---|---|
| adochiei_2025 | HL7 FHIR-Based Open-Source Framework for Real-Time Biomedical Signal Acquisition and IoMT Interoperability | Adochiei F.C. et al. | 2025 | Applied Sciences 15(23):12803 | 10.3390/app152312803 | 105024758728 | TL (HTML; the content of Table 3 was not captured) | `P/adochiei_2025.txt` |
| kim_2026 | A Comparative Performance Study of Parallel MQTT and RS485 Communication Architectures for High-Frequency IoT Sensing | Kim H.J. et al. | 2026 | Electronics 15(4):760 | 10.3390/electronics15040760 | 105031409367 | TL (HTML) | `P/kim_2026.txt` |
| lima_2025 | Evaluation of MQTT Bridge Architectures in a Cross-Organizational Context | Lima, Oyetoyan, Heldal, Hasselbring | 2025 | arXiv:2501.14890 (preprint) | – | – | TL | `P/lima_2025.pdf` |
| silva_2021 | A Performance Analysis of Internet of Things Networking Protocols: Evaluating MQTT, CoAP, OPC UA | da Silva, Carvalho, Soares, Sofia | 2021 | Applied Sciences 11(11):4879 | 10.3390/app11114879 | – | TL (HTML) | `P/silva_2021.txt` |
| reiher_2022 | Enabling Connectivity for Automated Mobility: A Novel MQTT-based Interface Evaluated in a 5G Case Study on Edge-Cloud Lidar Object Detection | Reiher, Lampe, Woopen et al. | 2022 | ICECCME 2022 (arXiv:2209.03630) | – | – | TL (§IV) | `P/reiher_2022.pdf` |
| saif_2022 | An Experimental Investigation of Tuning QUIC-Based Publish-Subscribe Architectures in IoT | Saif, Matrawy | 2022 | arXiv:2208.11178 (draft 2023) | – | – | TL (§VII) | `P/saif_2022.pdf` |
| escobedo_2026 (already in bib) | IoTHolter: An IoT Platform for Continuous Three-Lead ECG Monitoring Using Cellular Connectivity | Escobedo-Carranza et al. | 2026 | IoT 7(3):65 | 10.3390/iot7030065 | – | TL | `laporan/pustaka/escobedo_2026.pdf` |
| dasilva_2027 | Performance and Resilience Evaluation of a Hybrid Edge–Cloud IoT System Across Connected, Offline, and Reconnection Scenarios | da Silva L.F.A., Costa P.R.S.A., Schepke C. | 2027 | LNCS | 10.1007/978-3-032-30488-9_40 | 105044214888 | ABS | – |
| dearaujo_2026 | Reconfigurable ESP32-Based IoMT Architecture with End-to-End Latency Analysis over Wi-Fi with 5G Backhaul | De Araujo L.C. et al. | 2026 | IEEE MetroInd4.0&IoT 2026 | 10.1109/MetroInd4.0IoT69397.2026.11653168 | 105048839388 | JDL (paywall, preprint not found) | – |
| gaspar_2026 | The Price of Reliability: Stress-Testing MQTT in Practical IoT Communications | Gaspar L.M. et al. | 2026 | IEEE IoT Magazine | 10.1109/MIOT.2026.3681190 | 105038632755 | JDL (paywall) | – |

Key quotes:

- Adochiei §3.4: "Timestamps were instrumented at four conceptual measurement points ... (i) at the
  ESP32 publisher, (ii) upon broker reception, (iii) at InfluxDB write completion, and (iv) at data
  ingestion by Grafana ... The reported end-to-end latency excludes visualization-rendering time."
  / "no statistically meaningful confidence interval estimation or latency distribution analysis
  could be performed in this prototype."
- Adochiei §3.4.1: "Both ESP32 nodes were synchronized to a local NTP server (chrony on Ubuntu
  22.04, update interval 60 s), which maintained a drift of approximately ±5 ms over 60 s windows."
  §3.4.2: "a quantitative performance assessment was conducted across 10 consecutive acquisition
  cycles (60 s each). Key parameters ... were recorded and averaged."
- Kim 2026 Table 3 (client configuration): "QoS 1 ... mqtt_timeout 5 s Timeout for PUBACK or connection
  negotiation ... ntp_sync_interval 30 min". Table 8: "End-to-End Latency: Time elapsed from data
  generation at a sensor node to successful reception at the subscriber". Table 10: "Timestamp
  difference between sensor publish time and subscriber receive time | Clock synchronized via NTP".
  Table 11: mean 98 ms, maximum 210 ms, success rate 99.2%. §4.4.3: "The subscriber timestamp
  is recorded immediately upon message reception and before database insertion".
  Note: Kim's configuration (QoS 1, PUBACK timeout 5 s) is **identical** to ours, so this paper is
  the closest comparison.
- Lima 2025 §III-A, p. 4: "The end-to-end latency was measured by finding the difference between
  the time message was published by the gateway and the time the message was received by the
  subscriber". §III-B, p. 5: "Another (virtual) host machine ... was used to run the load driver
  and the subscriber to ensure the accuracy of the end-to-end delay measurements" / "Each benchmark
  parameter experiment was repeated 10 times" / "The ID was used to calculate the number of
  duplicated messages which could happen for the executions of the benchmark for QoS level 1".
- Silva 2021 §5: "all of the experiments have been repeated 10 times, and the values provided in
  this report correspond to the Average (AVG), Standard Deviation (STDEV), Maximum (MAX), Minimum
  (MIN), Median (MED), and Confidence Interval (IC)." Publisher on a laptop, subscriber on a Raspberry
  Pi, clock synchronisation not mentioned (TTC = t2 − t1 from two machines).
- Reiher 2022 §IV-B, p. 5: "while we set up the vehicle computer to synchronize its clock with
  the edge-cloud, the two clocks are not guaranteed to be synchronized exactly. Due to possible clock
  offsets, timestamps from vehicle and cloud cannot be compared directly". §IV-D, p. 6: "Our main
  performance-indicating metric is the mean of all measured latencies of a single 60 s experiment.
  Additionally, we also compute minimum, maximum, and median latency as well as the corrected
  standard deviation (jitter)."
- Saif 2022 §VII-A: "NetEm [25] was leveraged to emulate realistic resource-constrained IoT network
  conditions." Loss test: "NetEm rules were applied to drop outgoing packets on the client
  interface according to a uniform distribution ... ranged from 0 to 6%".
- Escobedo 2026 §3.2, p. 11: ESP32 over WiFi "resulting in 42 lost packets after transmitting
  approximately 3 million packets, corresponding to a loss rate of 0.001%". P. 12: "packet loss
  increases when the cellular signal strength fluctuates significantly". P. 15: "a comprehensive
  evaluation of end-to-end latency, jitter, buffering delay ... will be addressed in future work".
- da Silva 2027 (abstract): "evaluating the behavior of the edge node across three connectivity
  states: fully connected to the cloud, operating autonomously during disconnection, and during the
  reconnection phase with backlog synchronization ... quantitative analysis of throughput,
  end-to-end latency, resource consumption, and backlog draining time across progressively
  escalating load levels."
- Docker documentation, `docker container pause` (docs.docker.com/reference/cli/docker/container/pause/):
  on Linux it uses the cgroup freezer, "the process is unaware, and unable to capture, that it is being
  suspended, and subsequently resumed."

Other local sources examined: `resilient_edge_cloud.pdf` (Boluda-Prieto 2026) contains a PRISMA
review and a Kubernetes stress test, without a link-outage protocol that can be compared.
`yaacoub_2020.pdf` discusses DTN with daily delays, not a measurement methodology. `tipparaju_2021.pdf`
discusses BLE loss with a re-request mechanism; its PDF text was corrupted on extraction, so the method
is not quoted.

Not found / not verified:
- IEEE 11073-00101-2008 (RF wireless guidance for medical devices, DOI 10.1109/IEEESTD.2008.4736537):
  paywalled and withdrawn/inactive. Its latency table was not read.
- Sevin & Bayilmis (IAJIT 2021, "Table 1" ISO/IEEE 11073 categories) is said by the search result to contain
  a table of 11073 latency classes, but the server returned 503, so it was not read and not quoted.
- The "rule of three" (Hanley & Lippman-Hand 1983) and Clopper–Pearson 1934 were not read. The CI figures
  above were computed by ourselves with the exact Clopper–Pearson method (binomial inversion), not quoted.

---

## 3. Most important gaps (ordered from most risky at the defence)

1. **The latency definition is inconsistent in the book and differs from what was measured.** Chapter 3
   (tab:pengujian-pipeline) writes "waktu dari akuisisi hingga pembaruan dashboard" (time from acquisition to
   dashboard update) with the method "waktu tampil di ThingsBoard" (display time in ThingsBoard), and the
   Chapter 3 text writes "latensi rata-rata" (mean latency). What was measured is R-peak → row available in the
   **REST API** (dashboard rendering not included), then assessed on the **median**. An examiner can easily ask
   "what is the mean?" and "why not until the screen?". The fix is cheap: define the metric exactly as Adochiei
   §3.4 (render excluded), report mean ± SD, min, max next to the median (RFC 6703 §3.1 and §5.2), and use
   RFC 6703 to justify the median.
2. **The resilience test differs from the plan and was run only once.** The Chapter 3 plan is a "forced WiFi
   cut"; what was run is `docker pause` of the broker for 24 s, once. The pause only freezes the process, while
   the WiFi link and TCP stay alive, so the WiFi reconnect path has never been tested. The literature separates the
   offline and reconnect states and varies the load/backlog (da Silva 2027). Minimum: one AP-off test with ≥ 3
   repetitions and graded durations. If there is no time, state it as a limitation.
3. **The uncertainty of the latency measurement is not reported.** RFC 7679 §3.7 and §3.8.3 and RFC 7680
   §2.8.3 (MUST) require the degree of synchronisation and the calibration error to be reported. The existing
   components: the spread of the 5 offset samples, the possible ±50 ms bias from the sleep loop of the measurement
   tool, skew along the repetition (the offset is measured only at the start), and the polling resolution ≈ 100 ms
   + REST duration. Moreover, the term "lower bound" in the script is technically not a lower bound. One
   paragraph and one table row "uncertainty ±X ms" are enough. The 2 s target is not threatened because the gap
   from the median to the target is ±900 ms.
4. **The latency sample size is small for the tail, and has no CI.** n ±200–290 beats per repetition makes the
   p95 CI wide (n = 201: 185th to 198th order statistic), and this explains the p95 that swings 1,404–3,304 ms.
   Without re-measuring: report per 1-minute interval (Y.1541 §5.3.2) and the percentile CI. For PDSR our position
   is in fact strong: the pooled Clopper–Pearson CI is 99.02–99.97%.
5. **The deduplication claim is circular and the latency budget reference is not quite right.** "0 duplicate ts
   in ThingsBoard" is always 0 because of the upsert per ts, so the evidence must be taken on the broker/subscriber
   side (Lima 2025 uses the message ID). For the latency budget, Zhong 2022 (<250 ms) is BAN link latency, not
   E2E. Stronger references for 2 s are G.1010 (Responsive ~2 s; Table I.2 preferred < 2 s, acceptable < 4 s) and
   H.810 §6.1.7.5 (measured parameters ~1 s, alarm ~10 s). The Skorin-Kapov figures (<300 ms / <1 s) apply to
   emergency real-time ECG waveforms, while non-real-time telemonitoring is given "N.A.". Explain that what is sent
   is a label per beat.
