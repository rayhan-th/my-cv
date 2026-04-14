#!/usr/bin/env python3
"""Generate cv.typ for Rayhan Ahmed using the modern-cv Typst package."""

from pathlib import Path


def generate_cv():
    content = r"""#import "@preview/modern-cv:0.9.0": *

#fa-version("6")
#show "Résumé": "CV"

#show: resume.with(
  author: (
    firstname: "Rayhan",
    lastname: "Ahmed",
    email: "rayhan.thkoeln@gmail.com",
    phone: "(+49) 178-6957128",
    homepage: "https://rayhan-th.github.io/my-cv",
    github: "rayhan-th",
    address: "Deutzer Ring 5, 50679 Cologne, Germany",
    positions: (
      "Hydrologist",
      "GIS Specialist",
    ),
    custom: (
      (text: "LinkedIn", icon: "linkedin", link: "https://linkedin.com/in/rayhan95ahmed"),
      (text: "ResearchGate", icon: "researchgate", link: "https://researchgate.net/profile/Rayhan-Ahmed-4"),
    ),
  ),
  profile-picture: none,
  date: datetime.today().display(),
  language: "en",
  paper-size: "a4",
  accent-color: default-accent-color,
  colored-headers: true,
  show-footer: true,
)

#set text(font: "Arial", size: 10pt)
#set heading(bookmarked: true)
#set document(title: "Rayhan Ahmed - CV")

= Education

#resume-entry(
  title: [M.Sc. in Integrated Water Resources Management],
  location: [TH Köln, Cologne, Germany],
  date: [Sept 2023 -- ongoing],
  description: [GPA: 1.7 (after 90 ECTS) | DAAD Scholarship 2023--2025 | Master thesis ongoing],
)

#resume-item[
  - Key modules: GIS & Remote Sensing (1.3) · Flood Management (1.0) · Water System Analysis (1.3) · Water Resources Management (1.7) · Project Management (1.7) · Hydrology (2.0) · Hydraulic Infrastructure (2.7) · Urban Water Management (2.3)
]

#resume-entry(
  title: [M.Sc. in Disaster Science and Emergency Management],
  location: [Patuakhali Science and Technology University, Bangladesh],
  date: [2022],
  description: [GPA: 1.1 | *1st in cohort* | Focus: Research Methodology, Climate Adaptation, Water Resources Management],
)

#resume-entry(
  title: [B.Sc. in Disaster Management (Hons.)],
  location: [Patuakhali Science and Technology University, Bangladesh],
  date: [2019],
  description: [CGPA: 3.834 / 4.000 | *2nd in cohort* | Focus: Hydrology, GIS & Remote Sensing, Digital Photogrammetry, Spatial Database Analysis],
)

= Professional Experience

#resume-entry(
  title: [Intern & Master Thesis Student],
  location: [Thüringer Fernwasserversorgung (TFW), Erfurt, Germany],
  date: [May 2025 -- ongoing],
  description: [Technical Division | Reservoir Management (Hydrology)],
)

#resume-item[
  - Setup, calibration and application of hydrological models with TALSIM-NG for catchments Ziegenrück/Plothenbach and Neuer Teich
  - Comparison and validation of simulation results across TALSIM-NG, J2000, LUTZ and KOSTRA-REWANUS
  - GIS analysis and DEM processing for catchment delineation and land use planning
  - Python scripts for automated hydrological data processing and reporting
  - Participation in quarterly meetings, site visits and hydrometry measurements
  - Reference: _"zur vollsten Zufriedenheit"_ -- Thomas Dirkes, CEO, TFW (March 2026)
]

#resume-entry(
  title: [Research Consultant],
  location: [CEGIS, Ministry of Water Resources, Dhaka, Bangladesh],
  date: [Oct 2022 -- June 2023],
  description: [Center for Environmental & Geographic Information Services],
)

#resume-item[
  - Geospatial data analysis, GIS mapping and remote sensing for 15+ development projects (FAO, World Bank, BWDB)
  - Conducted Feasibility Studies, Environmental & Social Impact Assessments (EIA/ESIA) and Strategic Environmental Assessments (SEA)
  - UAV data collection and processing (certified practitioner, Nov 2023)
  - Stakeholder consultations: Focus Group Discussions (FGDs), Key Informant Interviews (KIIs), Stakeholder Consultation Meetings (SCMs)
]

#resume-entry(
  title: [Research Assistant],
  location: [IWFM, Bangladesh University of Engineering and Technology, Dhaka],
  date: [Feb 2021 -- June 2021],
  description: [Institute of Water and Flood Management],
)

#resume-item[
  - Field data collection, data processing and reporting under IDRC-funded project "Evaluation of Adaptation Trials in GBM-Delta (ADCF)"
]

#resume-entry(
  title: [Research Assistant],
  location: [Dept. of Emergency Management, PSTU, Patuakhali, Bangladesh],
  date: [July 2019 -- Oct 2022],
  description: [Faculty of Environmental Science and Disaster Management],
)

#resume-item[
  - Research support in disaster risk management, water resources and climate adaptation
  - GIS and remote sensing applications in flood risk, climate adaptation and disaster management research
]

= Technical Skills

#resume-skill-item(
  "GIS & Geodata",
  ("QGIS", "ArcGIS Pro", "Geodata preparation & analysis", "Catchment delineation", "DEM processing", "Land use planning", "UAV data collection (certified)"),
)

#resume-skill-item(
  "Hydrological Modelling",
  ("TALSIM-NG", "HEC-HMS", "Rainfall-runoff modelling", "Reservoir analysis", "Model calibration & validation", "J2000", "LUTZ", "KOSTRA-REWANUS"),
)

#resume-skill-item(
  "Remote Sensing",
  ("Satellite image analysis", "Digital photogrammetry", "Image processing", "Environmental monitoring"),
)

#resume-skill-item(
  "Programming",
  ("Python", "GeoPandas", "Rasterio", "Shapely", "NumPy", "Pandas", "Matplotlib", "Jupyter Notebook", "Geodata automation"),
)

#resume-skill-item(
  "Other Tools",
  ("Microsoft Teams", "Kanban Planner", "Canva", "MS Office"),
)

= Research and Publications

#resume-entry(
  title: [Peer-Reviewed Journal Articles],
  location: [],
  date: [],
  description: [],
)

#resume-item[
  - Ahmed, M.R., Mia, S., Sattar, M.A. et al. (2025). Chemical modification of biochar's functional groups enhances phosphate and arsenite adsorption. _SAINS TANAH -- Journal of Soil Science and Agroclimatology_, 22(1), pp. 203--219.
  - Mia, S., Roja, N.T., Sattar, M.A., Ahmed, R. et al. (2025). Prioritizing climate-smart agricultural technologies for coastal Bangladesh: A multicriteria assessment. _Agricultural Systems_, 230, p. 104489.
  - Parvez, A., Islam, M.T., Islam, M., Haque, M.F. & Ahmed, M.R. (2018). Environmental impact assessment of automatic brick manufacturing project at Lebukhali Dumki. _Journal of Environmental Science and Natural Resources_, 11(1--2), pp. 87--95.
]

#resume-entry(
  title: [Conference Paper],
  location: [],
  date: [Dec 2019],
  description: [],
)

#resume-item[
  - Ahmed, R., Mia, S. & Sattar, M.A. (2019). Surface functionalized biochar reduces arsenic contamination from soil: A batch study. _4th Young Scientists Congress_, December 2019, Bangladesh.
]

#resume-entry(
  title: [Master Thesis (ongoing)],
  location: [TH Köln / TFW Erfurt, Germany],
  date: [Nov 2025 -- ongoing],
  description: [Hydrological Assessment of Reservoir Catchments in Thuringia],
)

= Awards and Scholarships

#resume-item[
  - *2023--2025*: DAAD Scholarship -- German Academic Exchange Service, Germany
  - *2022*: 1st Place in Cohort -- M.Sc. Disaster Science and Emergency Management, PSTU
  - *2020*: National Science and Technology Fellowship -- Ministry of Science and Technology, Bangladesh
  - *2019*: 2nd Place in Cohort -- B.Sc. Disaster Management (Hons.), PSTU (CGPA: 3.834/4.0)
  - *2018--2019*: Dean's Merit Scholarship for Academic Excellence -- PSTU, Bangladesh
  - *2026*: Highest commendation reference _"zur vollsten Zufriedenheit"_ -- TFW Erfurt, Germany
]

= Languages

#resume-skill-item(
  "Languages",
  ("German: B2.1 (target C1)", "English: C1 -- IELTS 7.0 (L:7.5, R:6.5, W:6.5, S:7.0)", "Bengali: Native"),
)
"""
    return content


def main():
    base = Path(__file__).parent
    out_path = base / "cv.typ"
    content = generate_cv()
    out_path.write_text(content, encoding="utf-8")
    print(f"Generated {out_path} ({len(content):,} bytes)")


if __name__ == "__main__":
    main()
