# Market Viability Scorecard: AI Role-Match Hiring System

## Summary Scores

| Factor | Score (1-5) | Weight | Weighted |
|--------|-------------|--------|----------|
| **Market Size** | 3.5 | 25% | 0.875 |
| **Competition** | 2.5 | 25% | 0.625 |
| **Customer Pain** | 3.5 | 30% | 1.050 |
| **Monetization** | 2.5 | 20% | 0.500 |
| **TOTAL** | | 100% | **3.05/5** |

## Scoring Guide
- 5: Exceptional — strong signal to proceed
- 4: Good — worth pursuing
- 3: Acceptable — proceed with caution
- 2: Weak — significant concerns
- 1: Poor — likely not viable

---

## Key Findings

### Market Size (Agent 1) — Score: 3.5/5

- **TAM**: $169B talent acquisition market globally; $15.18B online recruitment tech
- **SAM**: $707-752M AI recruitment market (2025-2026), growing 6.8-7.6% CAGR
- **SOM**: $50K-$200K year 1, $500K-$2M year 3 (bootstrapped solopreneur reality)
- **Growth**: 7%+ CAGR for AI recruitment; 12.9% for broader online recruitment tech
- **Key trend**: 85% of employers adopting skills-based hiring; 87% already using AI in hiring; $2.3B invested in HR/recruitment startups in 2025
- **Verdict**: Large, growing market with clear demand. But realistic SOM is modest for a bootstrapped new entrant competing against $100M+ funded incumbents.

### Competition (Agent 2) — Score: 2.5/5

- **Direct competitors**: Eightfold AI ($410M funded, $2.1B valuation), HireVue ($293M funded, 70M+ interviews), SeekOut ($189M), Mercor ($350M Series C), Ashby ($116M)
- **Indirect**: Greenhouse (7,500+ customers), Lever, Workable, LinkedIn, Indeed — all adding AI features
- **Market gap**: No commercial product markets "job-to-job matching" as primary value prop
- **CRITICAL FINDING**: ConFit v2 (ACL 2025 paper) already implements the exact core insight — generating hypothetical representations to match in the same embedding space. The approach is published, open-source, and replicable.
- **Verdict**: Red-ocean market with deep-pocketed competitors. The "job-to-job matching" concept is a positioning angle, not a technical moat. Any competitor could add this as a feature. The Eightfold FCRA lawsuit creates a brief transparency window.

### Customer Pain (Agent 3) — Score: 3.5/5

- **Target persona**: Mid-market TA Lead (100-500 employees), secondarily recruiting agencies
- **Pain level**: 7/10 — 18+ hours/hire on screening, 27% TA burnout, $4,700+ cost per hire
- **Current solutions**: ATS keyword filters (94% of large companies), manual screening, LinkedIn Recruiter, staffing agencies
- **Willingness to pay**: $500-$2,000/month for mid-market; $200-$500/month for SMB
- **Key challenge**: HR buyers are hard to reach, sales cycles are long (2-12 months depending on company size), switching costs are high
- **Verdict**: Real, quantifiable pain that companies are already spending money to solve. But the buyer is an enterprise buyer, not a self-serve one. Requires sustained sales effort.

### Monetization (Agent 4) — Score: 2.5/5

- **Recommended model**: Hybrid subscription + per-screening usage ($299-$1,999/month tiers)
- **Price point**: $500-$800/month sweet spot for mid-market AI matching add-on
- **CAC estimate**: $410 (SMB) to $6,754 (enterprise); HR Tech average $450-$612
- **LTV estimate**: $3,588-$47,976 depending on tier
- **LTV:CAC**: 7-9:1 on paper (excellent), but unvalidated
- **Break-even**: 6-12 months to meaningful MRR (optimistic); 12-24 months realistic
- **Critical constraint**: William starts full-time job April 6, 2026. No sales team. No enterprise relationships. Current revenue focus is PT clients ($197/mo). Who acquires and supports customers?
- **Verdict**: Unit economics are viable in theory. Execution is the bottleneck — this is an enterprise/mid-market sales play that requires dedicated sales effort a solopreneur with a day job cannot sustain.

---

## Red Flags

1. **No technical moat**: The core innovation (vector space matching) is commoditized. ConFit v2 published the same approach in an ACL 2025 paper with open-source code. Any funded competitor could replicate this in weeks.

2. **Competitor firepower**: $2.3B invested in HR/recruitment AI startups in 2025 alone. Eightfold ($410M), Mercor ($350M), SeekOut ($189M) — these companies have 50-200+ engineers and dedicated sales teams.

3. **Enterprise sales motion required**: HR SaaS is not a product-led-growth market. Mid-market deals require demos, POCs, security reviews, procurement cycles. Average CAC is $450-$1,912. This takes time and relationships William doesn't have bandwidth for.

4. **Regulatory complexity**: California AI hiring regulations (Oct 2025), Colorado AI Act (Feb 2026), NYC Local Law 144 — compliance requires bias audits, record retention, and legal review. This adds significant product and legal complexity.

5. **Timing conflict**: William starts a full-time job (Collier County Wastewater, 7am-3pm) on April 6, 2026. Building, selling, and supporting an HR SaaS product on evenings and weekends while maintaining PT clients is an extremely heavy lift.

6. **Eightfold lawsuit precedent**: The Jan 2026 FCRA class action against Eightfold means ANY AI hiring tool that generates "applicant scores" without disclosure could face similar legal exposure. This is a liability risk.

---

## Opportunities

1. **Positioning angle**: "Job-to-job matching" is a compelling, easy-to-explain differentiator even if technically commoditized. Marketing this concept clearly could cut through the noise.

2. **Compliance-first positioning**: Post-Eightfold lawsuit, companies want transparent, explainable, auditable AI hiring. Building compliance/bias auditing as a core feature (not afterthought) could be a genuine differentiator.

3. **Integration play (not replacement)**: Don't build an ATS. Build a matching API/layer that integrates with Greenhouse, Lever, Ashby, etc. Smaller surface area, faster to build, easier to sell as a "plug-in."

4. **White-label for agencies**: Recruiting agencies (smaller buyers, faster decisions, less compliance overhead) could be a better initial market than direct enterprise sales.

5. **The concept could become a Marceau Solutions service offering**: Instead of a SaaS product, offer "AI-powered candidate screening" as a consulting service for the Digital Tower's AI services clients. Lower scale, higher margin, no product infrastructure needed.
