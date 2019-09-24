import csv
import pathlib
from itertools import groupby

from clldutils.path import Path
from pycldf import Wordlist
from pyglottolog import Glottolog
from pylexibank.dataset import Dataset as BaseDataset

CHANURL = "https://mpi-lingweb.shh.mpg.de/numeral/"

# FIXME: Point to Zenodo or GitHub API?
URL = "http://localhost:8000/cldf.zip"

# FIXME: Remove absolute path.
GLOTTOLOG_DIR = "/home/rzymski@shh.mpg.de/Repositories/glottolog/glottolog"

# Largest Glottolog families for sorting:
FAMILIES = [
    "Austronesian",
    "Atlantic-Congo",
    "Sino-Tibetan",
    "Indo-European",
    "Afro-Asiatic",
    "Nuclear Trans New Guinea",
    "Austroasiatic",
    "Tupian",
    "Tai-Kadai",
    "Mande",
    "Pama-Nyungan",
    "Dravidian",
    "Otomanguean",
    "Nilotic",
    "Turkic",
    "Uralic",
    "Central Sudanic",
    "Arawakan",
    "Nakh-Daghestanian",
    "Pano-Tacanan",
    "Uto-Aztecan",
    "Salishan",
    "Algic",
    "Cariban",
]


def make_index_link(s):
    stripped = s.strip("raw/")
    stripped_link = s.strip("raw/").replace(" ", "%20")
    return "* [" + stripped + "]" + "(" + stripped_link + ")"


def make_chan_link(s):
    s = s.replace(" ", "%20")
    return " ([Source]" + "(" + CHANURL + s + "))"


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "numerals"

    def cmd_download(self, **kw):
        index = Path(self.raw / "index.md")

        if index.exists():
            Path.unlink(index)

        channnumerals_files = [
            "cldf-metadata.json",
            "cognates.csv",
            "forms.csv",
            "languages.csv",
            "parameters.csv",
        ]

        glottolog = Glottolog(GLOTTOLOG_DIR)
        languoids = {l.id: l for l in glottolog.languoids()}

        self.raw.download_and_unpack(
            URL, *[Path("cldf", f) for f in channnumerals_files], log=self.log
        )

        channumerals = Wordlist.from_metadata("raw/cldf-metadata.json")

        """
        Create a list of list of ordered dictionaries, grouped by Language_ID, where each CLDF
        row is mapped to an individual entry.

        Example:  OrderedDict([('ID', 'amar1273-1-1'), ('Parameter_ID', '1'), ...])
        """
        split_ft = [
            list(f2)
            for f1, f2 in groupby(
                sorted(channumerals["FormTable"], key=lambda f1: (f1["Language_ID"])),
                lambda f1: (f1["Language_ID"]),
            )
        ]

        """
        This splits the list of forms into individual files, grouped by families (or Other for
        smaller families).
        """
        for entry in split_ft:
            lid = entry[0]["Language_ID"]
            chansrc = entry[0]["SourceFile"]
            fam = "Other"

            if languoids[lid].family and languoids[lid].family.name in FAMILIES:
                fam = languoids[lid].family.name

            pathlib.Path("raw/" + fam).mkdir(parents=True, exist_ok=True)

            with open("raw/" + fam + "/" + lid + ".csv", "w") as outfile:
                fp = csv.DictWriter(outfile, entry[0].keys())
                fp.writeheader()
                fp.writerows(sorted(entry, key=lambda x: int(x["Parameter_ID"])))
                github_file = outfile.name

            with open(index, "a+") as outfile:
                index_link = make_index_link(github_file)
                chan_link = make_chan_link(chansrc)
                outfile.write(index_link + chan_link + '\n')

    def cmd_install(self, **kw):
        with self.cldf as _:
            pass
