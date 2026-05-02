from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(30, 30, 60)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "NEXUS INSTITUTE OF ADVANCED RESEARCH - CLASSIFIED BULLETIN 2025", fill=True, ln=True, align="C")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Nexus Institute Bulletin 2025 - Page {self.page_no()}", align="C")

    def section(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(220, 230, 255)
        self.cell(0, 8, title, fill=True, ln=True)
        self.ln(2)

    def body(self, txt):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, txt)
        self.ln(3)

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# SCIENTISTS
pdf.section("SECTION 1: PIONEERING SCIENTISTS OF THE NEXUS PROGRAM")

pdf.body(
    "Dr. Elara Vonn (born 1978, Zurich) is the lead researcher behind the Vonn Entropic Compression "
    "theory, which proposes that information loss in black holes is reversible through quantum lattice "
    "mirroring. In 2023, Vonn published Reversible Entropy in Isolated Quantum Systems in the journal "
    "Nexus Physics Letters, winning the Bramwell Prize for Theoretical Physics. Her lab in the city of "
    "Halvard, Norway, uses a 400-qubit photonic processor named ORIN-7."
)

pdf.body(
    "Professor Tariq Mossad (born 1965, Cairo) discovered the Mossad-Chen Protein Fold, a previously "
    "unknown tertiary structure found exclusively in deep-sea organisms below 6,000 metres. His 2022 paper "
    "Abyss-Adapted Proteomics and the Mossad-Chen Fold demonstrated that this structure grants thermal "
    "stability up to 210 degrees C. Mossad leads the BioDepth Laboratory at the University of Aqaris."
)

pdf.body(
    "Dr. Senna Brightwell (born 1991, Melbourne) pioneered Neuromorphic Fractal Encoding (NFE), a "
    "technique that compresses neural network weights by 94% using fractal geometry without accuracy loss. "
    "Her startup BrightCore AI deployed NFE in edge devices across 47 countries by 2024. The encoding "
    "algorithm called FRAC-9 is open-source and stored in the Nexus Code Repository under license NX-44."
)

pdf.body(
    "Dr. Okafor Nweze (born 1983, Lagos) invented the Nweze Catalytic Stack, a room-temperature hydrogen "
    "fuel cell that achieves 91% efficiency using a bismuth-selenide membrane. The prototype codenamed "
    "HYDROS-1 produced 2.4 kW continuously for 800 hours in a 2024 field test at the Saharan Energy "
    "Research Park in Oujda, Morocco. Nweze holds 14 patents related to green hydrogen technology."
)

# CITIES
pdf.add_page()
pdf.section("SECTION 2: CITIES AT THE FRONTIER OF SCIENCE AND TECHNOLOGY")

pdf.body(
    "Halvard, Norway (population 42,000) - Often called the Silicon Fjord, Halvard hosts 12 quantum "
    "computing labs and the annual Nexus Summit. The city runs entirely on tidal-generated electricity and "
    "has a carbon capture facility that sequesters 800 tonnes of CO2 daily. Mayor Ingrid Solberg launched "
    "the Halvard Smart Grid Initiative in 2023, reducing energy waste by 38%."
)

pdf.body(
    "Aqaris, Jordan (population 180,000) - A planned research city completed in 2019 near the Dead Sea, "
    "Aqaris was designed by architect Zora Mehmed using bio-inspired hexagonal urban blocks. The city uses "
    "the Desalination Loop, a closed-cycle system that recycles 99.2% of wastewater. Aqaris hosts the "
    "World Proteomics Congress every two years and the Deep Ocean Data Centre (DODC)."
)

pdf.body(
    "Veltran, Canada (population 67,000) - Located in northern Ontario, Veltran emerged around the "
    "discovery of veltranite, a rare earth mineral that conducts electricity at -40 degrees C without "
    "resistance. The Veltran Mineral Authority exports 3,200 tonnes annually to chip manufacturers. "
    "The city's Cryotech Museum holds the world's only naturally occurring veltranite crystal exceeding 40 kg."
)

pdf.body(
    "Solindra City, Chile (population 95,000) - Built at 4,200 metres altitude in the Atacama plateau, "
    "Solindra City is home to the Southern Hemisphere Quantum Observatory (SHQO) and six photovoltaic "
    "farms generating 14 GW combined. Founded in 2017 by the Nexus Energy Consortium, it achieved "
    "net-zero emissions in 2021. Chief Scientist Dr. Lucia Tern coordinates all energy-to-compute research."
)

# RESEARCH FINDINGS
pdf.add_page()
pdf.section("SECTION 3: BREAKTHROUGH RESEARCH FINDINGS (2023-2025)")

pdf.body(
    "FINDING NX-001: Vonn Entropic Mirror Effect\n"
    "Elara Vonn's team confirmed that photon pairs entangled inside ORIN-7 maintained coherence for "
    "14.7 milliseconds at room temperature - 300x longer than the previous record. This was achieved "
    "using a novel entropic mirror substrate made of graphene layered with hafnium dioxide. The result "
    "was published on 14 March 2024 and independently replicated by teams in Aqaris and Halvard."
)

pdf.body(
    "FINDING NX-002: FRAC-9 Edge Deployment Benchmark\n"
    "BrightCore AI released benchmark results showing FRAC-9 running a 70-billion-parameter language "
    "model on a device with only 512 MB of RAM at 18 tokens per second. The model achieved 96.3% of "
    "the original accuracy on the Nexus NLP Benchmark Suite NNBS-v4. This is the first time a 70B "
    "model has been deployed on consumer-grade IoT hardware without quantisation."
)

pdf.body(
    "FINDING NX-003: HYDROS-1 Grid Integration Test\n"
    "The Nweze Catalytic Stack passed IEC 62282-7-1 safety standard in January 2025, making it the "
    "first room-temperature hydrogen cell certified for residential installation. Field tests in Veltran "
    "show 200 HYDROS-1 units can power 400 homes for 72 hours on a single hydrogen cartridge. The "
    "bismuth-selenide membrane costs $4.20 per unit at scale, versus $140 for platinum-based membranes."
)

pdf.body(
    "FINDING NX-004: Mossad-Chen Fold Industrial Application\n"
    "Tariq Mossad's team synthesised an artificial version of the Mossad-Chen Fold protein using "
    "directed evolution in 2024. The synthetic variant MCF-S3 can encapsulate and neutralise PFAS "
    "chemicals in water at 99.7% efficiency within 4 hours at room temperature. The Aqaris Water "
    "Authority began a pilot treating 50,000 litres daily at the Aqaris Eastern Reservoir."
)

pdf.body(
    "FINDING NX-005: Veltranite Superconductor Discovery\n"
    "A joint team from Veltran and Solindra City confirmed in February 2025 that veltranite doped "
    "with 3% osmium achieves superconductivity at -18 degrees C - the highest recorded superconducting "
    "temperature for a naturally occurring mineral compound. Codenamed VELT-OS3, this material could "
    "enable lossless transcontinental power transmission. The discovery won the Nexus Grand Prize 2025, "
    "a $5 million research grant - the institute's highest honour."
)

# GLOSSARY
pdf.add_page()
pdf.section("SECTION 4: QUICK REFERENCE GLOSSARY")

terms = [
    ("Vonn Entropic Compression", "Theory by Dr. Elara Vonn: entropy loss in quantum systems reversed via lattice mirroring."),
    ("ORIN-7", "400-qubit photonic quantum processor operated by Vonn Lab in Halvard, Norway."),
    ("Mossad-Chen Fold", "Novel protein structure found in deep-sea life, stable up to 210C. Discovered by Prof. Tariq Mossad."),
    ("MCF-S3", "Synthetic Mossad-Chen Fold variant that removes PFAS chemicals from water at 99.7% efficiency."),
    ("Neuromorphic Fractal Encoding (NFE)", "AI compression by Dr. Senna Brightwell: 94% weight reduction without accuracy loss."),
    ("FRAC-9", "Open-source NFE algorithm, licence NX-44, Nexus Code Repository."),
    ("HYDROS-1", "Room-temperature hydrogen fuel cell by Dr. Okafor Nweze, 91% efficiency, bismuth-selenide membrane."),
    ("Veltranite", "Rare earth mineral from Veltran, Canada; superconductive at -18C when doped with 3% osmium (VELT-OS3)."),
    ("SHQO", "Southern Hemisphere Quantum Observatory, Solindra City, Chile, altitude 4,200 m."),
    ("NNBS-v4", "Nexus NLP Benchmark Suite v4, standard for evaluating compressed AI models."),
    ("Nexus Grand Prize 2025", "$5 million research grant, highest honour from Nexus Institute. Won by VELT-OS3 team."),
    ("Halvard Smart Grid Initiative", "Programme by Mayor Ingrid Solberg that cut Halvard energy waste by 38% in 2023."),
    ("Bramwell Prize", "Top award in Theoretical Physics given to Dr. Elara Vonn for entropic compression research."),
    ("BioDepth Laboratory", "Research lab at University of Aqaris led by Prof. Tariq Mossad, specialising in deep-sea biology."),
    ("BrightCore AI", "Startup by Dr. Senna Brightwell that deployed FRAC-9 edge AI across 47 countries by 2024."),
]

for term, definition in terms:
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(55, 6, term, ln=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, f": {definition}")
    pdf.ln(1)

out = "data/raw/nexus_research_bulletin_2025.pdf"
pdf.output(out)
print(f"PDF created: {out}")
