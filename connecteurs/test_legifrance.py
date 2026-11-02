# -*- coding: utf-8 -*-
"""Tests de legifrance.py qui ne demandent ni réseau ni identifiants PISTE.

Lancement, depuis la racine du dépôt :
    python -m unittest discover -s connecteurs -v
"""
import ast
import unittest
from unittest import mock

import legifrance


class NumerosCherches(unittest.TestCase):
    """_art_candidates : les numéros essayés auprès de Légifrance, du plus précis au plus général."""

    ATTENDUS = {
        "L. 314-11 8°": ["L314-11", "L314"],
        "158-5-a": ["158-5-a", "158-5", "158"],
        "L. 181-18": ["L181-18", "L181"],
        "R. 122-5": ["R122-5", "R*122-5", "R122", "R*122"],
        "6": ["6"],
        "238 quindecies": ["238 quindecies", "238quindecies"],
        "L. 54 A": ["L54 A", "L54A"],
        "": [],
        None: [],
    }

    def test_designations_sans_prefixe(self):
        for article, attendu in self.ATTENDUS.items():
            with self.subTest(article=article):
                self.assertEqual(legifrance._art_candidates(article), attendu)

    def test_prefixe_article_retire(self):
        for article in ["Article L. 181-18", "article L. 181-18", "ARTICLE L. 181-18",
                        "art. L. 181-18", "Art. L. 181-18", "art L. 181-18", "art.L. 181-18",
                        "l'article L. 181-18", "l’article L. 181-18", "  Article  L. 181-18 "]:
            with self.subTest(article=article):
                self.assertEqual(legifrance._art_candidates(article), ["L181-18", "L181"])

    def test_article_de_loi(self):
        for article in ["article 6", "Article 6", "art. 6"]:
            with self.subTest(article=article):
                self.assertEqual(legifrance._art_candidates(article), ["6"])


class MemeArticle(unittest.TestCase):
    """_meme_article : la désignation demandée et le numéro renvoyé par Légifrance coïncident-ils ?"""

    IDENTIQUES = [
        ("L. 321-3", "L321-3"),
        ("L. 314-11 8°", "L314-11"),
        ("Article L. 181-18", "L181-18"),
        ("art. L. 181-18", "L181-18"),
        ("l'article R. 181-28", "R181-28"),
        ("article 6", "6"),
        ("Article 6", "6"),
    ]

    DIFFERENTS = [
        ("L. 181-18-1", "L181-18"),
        ("Article L. 181-18-1", "L181-18"),
        ("article 55-1", "55"),
        ("158-5-a", "158"),
        ("", ""),
    ]

    def test_identiques(self):
        for demande, rendu in self.IDENTIQUES:
            with self.subTest(demande=demande, rendu=rendu):
                self.assertTrue(legifrance._meme_article(demande, rendu))

    def test_differents(self):
        for demande, rendu in self.DIFFERENTS:
            with self.subTest(demande=demande, rendu=rendu):
                self.assertFalse(legifrance._meme_article(demande, rendu))


def faux_post(num_rendu):
    """Substitut de `_post` : Légifrance renvoie toujours l'article `num_rendu`, quel que soit le
    numéro cherché, comme lorsque la cascade retombe sur un article voisin. Identifiants fictifs."""
    def _post(chemin, charge):
        if chemin == "/search" and charge.get("fond") == "LODA_DATE":
            return {"results": [{"titles": [{"id": "LEGITEXT000000000002",
                                             "title": "Loi n° 78-17 du 6 janvier 1978"}]}]}
        if chemin == "/search":
            return {"results": [{"id": "LEGIARTI000000000001"}]}
        if chemin == "/consult/legiPart":
            return {"sections": [{"articles": [{"id": "LEGIARTI000000000003", "num": num_rendu,
                                                "content": "<p>Texte.</p>"}]}]}
        if chemin == "/consult/getArticle":
            return {"article": {"id": charge["id"], "num": num_rendu, "texte": "Texte.",
                                "articleVersions": []}}
        raise AssertionError("appel inattendu : " + chemin)
    return _post


class ResoudreExact(unittest.TestCase):
    """Paramètre `exact` de `resoudre` et `resoudre_loi`, et son usage par `historique_article`.

    `_post` est remplacé par `faux_post` et le catalogue des codes par une liste fixe :
    aucun appel n'atteint PISTE, aucun fichier n'est écrit."""

    CODE = "Code de l'environnement"
    LOI = "loi n° 78-17"

    def setUp(self):
        for patch in (mock.patch.object(legifrance, "_CODES_MAP", {"code de l'environnement": self.CODE}),
                      mock.patch.dict(legifrance._TOC_CACHE, clear=True)):
            patch.start()
            self.addCleanup(patch.stop)

    def resoudre(self, num_rendu, *args, **kwargs):
        with mock.patch.object(legifrance, "_post", faux_post(num_rendu)):
            return legifrance.resoudre(*args, **kwargs)

    def test_code_par_defaut_inexact_rendu(self):
        r = self.resoudre("L181-18", self.CODE, "L. 181-18-1", "2024-03-15")
        self.assertTrue(r["trouve"])
        self.assertFalse(r["exact"])

    def test_code_exact_true_inexact_ecarte(self):
        r = self.resoudre("L181-18", self.CODE, "L. 181-18-1", "2024-03-15", exact=True)
        self.assertFalse(r["trouve"])
        self.assertFalse(r["exact"])
        self.assertEqual(r["num"], "L181-18")
        self.assertEqual(r["lien"], "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000000000001")

    def test_code_exact_true_article_exact_rendu(self):
        r = self.resoudre("L181-18-1", self.CODE, "L. 181-18-1", "2024-03-15", exact=True)
        self.assertTrue(r["trouve"])
        self.assertTrue(r["exact"])

    def test_loi_exact_true_inexact_ecarte(self):
        r = self.resoudre("6", self.LOI, "article 6-1", "2024-03-15", exact=True)
        self.assertFalse(r["trouve"])
        self.assertFalse(r["exact"])
        self.assertEqual(r["num"], "6")

    def test_loi_par_defaut_inexact_rendu(self):
        r = self.resoudre("6", self.LOI, "article 6-1", "2024-03-15")
        self.assertTrue(r["trouve"])
        self.assertFalse(r["exact"])

    def test_historique_inexact_ecarte(self):
        with mock.patch.object(legifrance, "_post", faux_post("L181-18")):
            h = legifrance.historique_article(self.CODE, "L. 181-18-1", "2024-03-15")
        self.assertEqual(h, {"trouve": False, "exact": False, "num": "L181-18",
                             "lien": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000000000001"})

    def test_historique_exact_poursuivi(self):
        with mock.patch.object(legifrance, "_post", faux_post("L181-18-1")):
            h = legifrance.historique_article(self.CODE, "L. 181-18-1", "2024-03-15")
        self.assertTrue(h["trouve"])
        self.assertEqual(h["versions"], [])


class PanneDePiste(Exception):
    """Erreur simulée : PISTE ne répond pas."""


def post_en_panne(chemin_en_panne, num_rendu="L181-18", fond=None, a_partir_de=1, versions=()):
    """Substitut de `_post` qui lève `PanneDePiste` sur `chemin_en_panne` (et, si `fond` est
    donné, seulement pour ce fonds), à partir du `a_partir_de`-ième appel à ce chemin ; les autres
    appels répondent comme `faux_post`. `versions` : versions renvoyées par getArticle."""
    normal = faux_post(num_rendu)
    compte = {"n": 0}

    def _post(chemin, charge):
        if chemin == chemin_en_panne and (fond is None or charge.get("fond") == fond):
            compte["n"] += 1
            if compte["n"] >= a_partir_de:
                raise PanneDePiste("503 Service Unavailable")
        reponse = normal(chemin, charge)
        if chemin == "/consult/getArticle" and versions:
            reponse["article"]["articleVersions"] = list(versions)
        return reponse
    return _post


class Pannes(unittest.TestCase):
    """Une panne de PISTE est signalée par le champ `panne`, et non confondue avec une absence."""

    CODE = "Code de l'environnement"
    LOI = "loi n° 78-17"

    def setUp(self):
        for patch in (mock.patch.object(legifrance, "_CODES_MAP", {"code de l'environnement": self.CODE}),
                      mock.patch.dict(legifrance._TOC_CACHE, clear=True),
                      mock.patch.dict(legifrance.DERNIERE_PANNE, {"quand": None, "quoi": None, "nombre": 0})):
            patch.start()
            self.addCleanup(patch.stop)

    def appeler(self, faux, fonction, *args, **kwargs):
        with mock.patch.object(legifrance, "_post", faux):
            return fonction(*args, **kwargs)

    def test_loi_non_identifiee_panne(self):
        r = self.appeler(post_en_panne("/search", fond="LODA_DATE"),
                         legifrance.resoudre_loi, self.LOI, "article 6", "2024-03-15")
        self.assertFalse(r["trouve"])
        self.assertIn("503", r["panne"])

    def test_loi_plan_panne(self):
        r = self.appeler(post_en_panne("/consult/legiPart"),
                         legifrance.resoudre_loi, self.LOI, "article 6", "2024-03-15")
        self.assertFalse(r["trouve"])
        self.assertIn("503", r["panne"])

    def test_loi_absente_sans_panne(self):
        def sans_resultat(chemin, charge):
            return {"results": []}
        r = self.appeler(sans_resultat, legifrance.resoudre_loi, self.LOI, "article 6", "2024-03-15")
        self.assertFalse(r["trouve"])
        self.assertNotIn("panne", r)

    def test_historique_loi_panne(self):
        h = self.appeler(post_en_panne("/search", fond="LODA_DATE"),
                         legifrance.historique_article, self.LOI, "article 6", "2024-03-15")
        self.assertFalse(h["trouve"])
        self.assertIn("503", h["panne"])

    def test_historique_article_panne(self):
        # 1er getArticle : dans `resoudre` ; 2e : dans `historique_article`, en panne
        h = self.appeler(post_en_panne("/consult/getArticle", num_rendu="L181-18", a_partir_de=2),
                         legifrance.historique_article, self.CODE, "L. 181-18", "2024-03-15")
        self.assertEqual(h, {"trouve": False, "panne": "503 Service Unavailable"})

    def test_historique_version_panne(self):
        # 3e getArticle, celui de la version, en panne : l'historique est renvoyé, avec `panne`
        version = {"id": "LEGIARTI000000000004", "version": "1.0", "dateDebut": None, "dateFin": None}
        h = self.appeler(post_en_panne("/consult/getArticle", num_rendu="L181-18", a_partir_de=3,
                                       versions=[version]),
                         legifrance.historique_article, self.CODE, "L. 181-18", "2024-03-15")
        self.assertTrue(h["trouve"])
        self.assertIn("503", h["panne"])
        self.assertIsNone(h["versions"][0]["modif"])

    def test_historique_sans_panne(self):
        h = self.appeler(faux_post("L181-18"), legifrance.historique_article,
                         self.CODE, "L. 181-18", "2024-03-15")
        self.assertTrue(h["trouve"])
        self.assertNotIn("panne", h)

    def test_subdivision_de_code_panne(self):
        r = self.appeler(post_en_panne("/search"), legifrance.resoudre_subdivision,
                         "code", self.CODE, [("titre", "Ier")], "2024-03-15")
        self.assertFalse(r["trouve"])
        self.assertIn("503", r["panne"])

    def test_compteur_de_pannes(self):
        for _ in range(2):
            self.appeler(post_en_panne("/consult/legiPart"),
                         legifrance.resoudre_loi, self.LOI, "article 6", "2024-03-15")
        self.assertEqual(legifrance.DERNIERE_PANNE["nombre"], 2)


class DateDeFin(unittest.TestCase):
    """_iso_fin : la date conventionnelle du 1er janvier 2999 (et au-delà) veut dire « pas de fin »."""

    def test_date_sans_terme(self):
        for date in ("2999-01-01", "2999-12-31", "3000-01-01"):
            with self.subTest(date=date):
                self.assertIsNone(legifrance._iso_fin(legifrance._ms(date)))
        self.assertEqual(legifrance._ms("2999-01-01"), 32472144000000)

    def test_vraies_dates_conservees(self):
        for date in ("2027-01-01", "2023-03-12", "2998-12-31"):
            with self.subTest(date=date):
                self.assertEqual(legifrance._iso_fin(legifrance._ms(date)), date)

    def test_date_absente(self):
        self.assertIsNone(legifrance._iso_fin(None))

    def test_resoudre_version_en_vigueur(self):
        def faux_post(chemin, charge):
            if chemin == "/search":
                return {"results": [{"id": "LEGIARTI000000000001"}]}
            return {"article": {"id": charge["id"], "num": "L181-18", "texte": "Texte.",
                                "dateDebut": legifrance._ms("2023-03-12"), "dateFin": 32472144000000}}
        with mock.patch.object(legifrance, "_CODES_MAP", {"code de l'environnement": "Code de l'environnement"}), \
             mock.patch.object(legifrance, "_post", faux_post):
            r = legifrance.resoudre("Code de l'environnement", "L. 181-18", "2024-03-15")
        self.assertEqual(r["version_debut"], "2023-03-12")
        self.assertIsNone(r["version_fin"])


class ConversionDesDates(unittest.TestCase):
    """_iso : millisecondes -> date, sans `utcfromtimestamp` (obsolète) ni limite de plateforme."""

    def test_dates(self):
        for date in ("2024-03-15", "1970-01-02", "1804-03-21", "2999-01-01"):
            with self.subTest(date=date):
                self.assertEqual(legifrance._iso(legifrance._ms(date)), date)

    def test_date_absente(self):
        self.assertIsNone(legifrance._iso(None))

    def test_sans_avertissement_d_obsolescence(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            legifrance._iso(legifrance._ms("2024-03-15"))


class TermesDeRecherche(unittest.TestCase):
    """chercher_termes envoie à Légifrance les termes séparés par des espaces, qu'ils soient
    donnés en liste ou en une seule chaîne (forme de l'exemple du README)."""

    def valeur_envoyee(self, termes):
        charges = []
        with mock.patch.object(legifrance, "_post", lambda chemin, charge: charges.append(charge) or {}):
            legifrance.chercher_termes(termes)
        return charges[0]["recherche"]["champs"][0]["criteres"][0]["valeur"] if charges else None

    def test_chaine(self):
        self.assertEqual(self.valeur_envoyee("obligation de motivation refus protection fonctionnelle"),
                         "obligation de motivation refus protection fonctionnelle")

    def test_liste(self):
        self.assertEqual(self.valeur_envoyee(["obligation de motivation", "protection fonctionnelle"]),
                         "obligation de motivation protection fonctionnelle")

    def test_sans_terme_pas_de_requete(self):
        for termes in ("", "   ", [], None):
            with self.subTest(termes=termes):
                self.assertIsNone(self.valeur_envoyee(termes))


def lien(type_, orientation, cid, date, titre=None):
    """Lien de modification au format de /consult/getArticle. Identifiants et titres fictifs."""
    return {"linkType": type_, "linkOrientation": orientation, "textCid": cid,
            "datePubliTexte": date, "textTitle": titre or "Texte " + cid[-2:], "natureText": "LOI"}


class TextesDeVersion(unittest.TestCase):
    """textes_de_version : les textes qui ont produit une version, sans hiérarchie.
    Les cas reprennent la forme des liens constatés le 02/11/2026 ; identifiants fictifs."""

    CODIF_1 = lien("CODIFICATION", "source", "JORFTEXT000000000011", "2000-09-21")
    CODIF_2 = lien("CODIFICATION", "source", "JORFTEXT000000000012", "2003-07-03")

    def cids(self, liens):
        return [l["textCid"] for l in legifrance.textes_de_version(liens)]

    def test_version_ancienne_codification_ecartee(self):
        # Forme de l'article L. 512-1 du code de l'environnement, version du 31/07/2003 : deux
        # liens de codification, et la loi qui a produit la version, citée pour deux articles.
        liens = [self.CODIF_1, self.CODIF_2,
                 lien("MODIFICATION", "source", "JORFTEXT000000000013", "2003-07-31"),
                 lien("MODIFICATION", "source", "JORFTEXT000000000013", "2003-07-31")]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000013"])

    def test_creation_ancienne(self):
        # Forme de l'article L. 521-1 du code de justice administrative : la loi qui a créé
        # l'article, et non l'ordonnance qui a codifié la partie législative.
        liens = [self.CODIF_1, lien("CREATION", "source", "JORFTEXT000000000014", "2000-07-01"),
                 self.CODIF_2]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000014"])

    def test_version_recente_codification_ecartee(self):
        # Forme de l'article 1240 du code civil, version du 01/10/2016.
        liens = [lien("MODIFIE", "cible", "JORFTEXT000000000015", "2016-02-11"), self.CODIF_1]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000015"])

    def test_plusieurs_textes_par_date(self):
        # Forme de l'article L. 123-2 du code de l'environnement, version du 10/08/2016 : deux
        # textes, renvoyés tous deux, du plus ancien au plus récent.
        liens = [lien("MODIFIE", "cible", "JORFTEXT000000000017", "2016-08-09"),
                 lien("MODIFIE", "cible", "JORFTEXT000000000016", "2016-08-05")]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000016", "JORFTEXT000000000017"])

    def test_meme_texte_une_fois(self):
        # Forme de l'article L. 411-2 du code de l'environnement : une loi citée pour trois articles.
        liens = [lien("MODIFIE", "cible", "JORFTEXT000000000018", "2016-08-09") for _ in range(3)]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000018"])

    def test_textes_modifies_par_l_article_ecartes(self):
        # Article de loi : orientés « source », CREE et MODIFIE désignent les textes que CET article
        # crée ou modifie (forme de l'article 2 de la loi n° 2018-148).
        liens = [lien("MODIFIE", "source", "JORFTEXT000000000019", "2018-03-03"),
                 lien("CREE", "source", "JORFTEXT000000000020", "2018-03-03"),
                 lien("MODIFIE", "cible", "JORFTEXT000000000021", "2019-01-01")]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000021"])

    def test_codification_seule(self):
        # Version d'origine d'un article codifié : seuls les liens de codification restent.
        self.assertEqual(self.cids([self.CODIF_2, self.CODIF_1]),
                         ["JORFTEXT000000000011", "JORFTEXT000000000012"])

    def test_autre_type_a_defaut(self):
        liens = [lien("TRANSFERE", "cible", "JORFTEXT000000000022", "2010-01-01")]
        self.assertEqual(self.cids(liens), ["JORFTEXT000000000022"])

    def test_aucun_texte(self):
        for liens in (None, [], [{"linkType": "MODIFIE", "linkOrientation": "cible"}]):
            with self.subTest(liens=liens):
                self.assertEqual(legifrance.textes_de_version(liens), [])


class Abrogation(unittest.TestCase):
    """Une abrogation désigne le texte qui a clos la version : jamais retenue."""

    def test_abrogation_seule(self):
        for type_ in ("ABROGATION", "ABROGE"):
            with self.subTest(type_=type_):
                self.assertEqual(legifrance.textes_de_version(
                    [lien(type_, "source", "JORFTEXT000000000030", "2000-09-21")]), [])

    def test_abrogation_et_autre_type(self):
        liens = [lien("ABROGATION", "source", "JORFTEXT000000000030", "2000-09-21"),
                 lien("TRANSFERE", "cible", "JORFTEXT000000000031", "1999-01-01")]
        self.assertEqual([l["textCid"] for l in legifrance.textes_de_version(liens)],
                         ["JORFTEXT000000000031"])


def concordance(type_, orientation, article_id, titre, cid="JORFTEXT000000000040", nature="LOI"):
    """Référence de concordance au format de /consult/getArticle. Identifiants fictifs."""
    return {"linkType": type_, "linkOrientation": orientation, "articleId": article_id,
            "textTitle": titre, "textCid": cid, "natureText": nature}


class OrigineCodification(unittest.TestCase):
    """origine_codification et textes_produisant : remonter de la codification à la disposition
    d'origine. Forme des réponses constatée le 02/11/2026 ; identifiants et titres fictifs."""

    CODIF = [lien("CODIFICATION", "source", "JORFTEXT000000000011", "2000-09-21"),
             lien("CODIFICATION", "source", "JORFTEXT000000000012", "2003-07-03")]
    DATE_CODIF = legifrance._ms("2000-09-21")

    def article_codifie(self, *concordances):
        return {"id": "LEGIARTI000000000100", "dateDebut": self.DATE_CODIF,
                "lienModifications": self.CODIF, "lienConcordes": list(concordances)}

    def appeler(self, articles, fonction, *args):
        """`articles` : réponses de getArticle, par identifiant."""
        def _post(chemin, charge):
            self.assertEqual(chemin, "/consult/getArticle")
            return {"article": articles[charge["id"]]}
        with mock.patch.object(legifrance, "_post", _post):
            return fonction(*args)

    def test_disposition_modifiee_avant_codification(self):
        # Forme de L. 512-1 du code de l'environnement : issu de l'article 3 de la loi n° 76-663,
        # modifié en 1993 ; c'est la loi de 1993 qui a produit la rédaction codifiée.
        ancien = {"id": "LEGIARTI000000000201", "dateDebut": legifrance._ms("1977-01-01"),
                  "articleVersions": [
                      {"id": "LEGIARTI000000000201", "dateDebut": legifrance._ms("1977-01-01"),
                       "dateFin": legifrance._ms("1993-01-04")},
                      {"id": "LEGIARTI000000000202", "dateDebut": legifrance._ms("1993-01-04"),
                       "dateFin": self.DATE_CODIF}]}
        version_1993 = {"id": "LEGIARTI000000000202", "lienModifications": [
            lien("MODIFICATION", "source", "JORFTEXT000000000041", "1993-01-05"),
            lien("ABROGATION", "source", "JORFTEXT000000000011", "2000-09-21")]}
        article = self.article_codifie(
            concordance("CONCORDANCE", "source", "JORFTEXT000000000040", "Loi fictive 76 art. 3"),
            concordance("CONCORDE", "cible", "LEGIARTI000000000201", "Loi fictive 76 - art. 3 (Ab)"))
        r = self.appeler({"LEGIARTI000000000201": ancien, "LEGIARTI000000000202": version_1993},
                         legifrance.origine_codification, article)
        self.assertEqual([l["textCid"] for l in r["textes"]], ["JORFTEXT000000000041"])
        self.assertEqual(r["chemin"], ["Loi fictive 76 - art. 3 (Ab)"])

    def test_redaction_d_origine(self):
        # Forme de L. 123-2 : l'article 1er de la loi n° 83-630, jamais modifié, ne porte que son
        # abrogation ; le texte retenu est la loi qui le contient.
        ancien = {"id": "LEGIARTI000000000301", "lienModifications": [
            lien("ABROGATION", "source", "JORFTEXT000000000011", "2000-09-21")]}
        article = self.article_codifie(
            concordance("CONCORDE", "cible", "LEGIARTI000000000301", "Loi fictive 83 - art. 1 (Ab)",
                        cid="JORFTEXT000000000042"))
        r = self.appeler({"LEGIARTI000000000301": ancien}, legifrance.origine_codification, article)
        self.assertEqual([l["textCid"] for l in r["textes"]], ["JORFTEXT000000000042"])

    def test_ancien_code_remonte(self):
        # Une disposition d'un ancien code, elle-même seulement codifiée, est remontée à son tour.
        code_ancien = {"id": "LEGIARTI000000000401", "lienModifications": self.CODIF[:1],
                       "lienConcordes": [concordance("CONCORDE", "cible", "LEGIARTI000000000402",
                                                     "Loi fictive 76 - art. 4 (Ab)")]}
        loi = {"id": "LEGIARTI000000000402", "lienModifications": [
            lien("MODIFICATION", "source", "JORFTEXT000000000043", "1985-01-01")]}
        article = self.article_codifie(
            concordance("CONCORDE", "cible", "LEGIARTI000000000401", "Code fictif - art. L1 (Ab)",
                        cid="LEGITEXT000000000044", nature="CODE"))
        r = self.appeler({"LEGIARTI000000000401": code_ancien, "LEGIARTI000000000402": loi},
                         legifrance.origine_codification, article)
        self.assertEqual([l["textCid"] for l in r["textes"]], ["JORFTEXT000000000043"])
        self.assertEqual(r["chemin"], ["Code fictif - art. L1 (Ab)", "Loi fictive 76 - art. 4 (Ab)"])

    def test_concordance_vers_le_nouveau_code_ignoree(self):
        article = self.article_codifie(
            concordance("CONCORDE", "source", "LEGIARTI000000000501", "Code fictif - art. L2 (V)"))
        r = self.appeler({}, legifrance.origine_codification, article)
        self.assertEqual(r, {"textes": [], "chemin": []})

    def test_boucle_bornee(self):
        boucle = {"id": "LEGIARTI000000000601", "lienModifications": self.CODIF[:1],
                  "lienConcordes": [concordance("CONCORDE", "cible", "LEGIARTI000000000601", "Boucle")]}
        r = self.appeler({"LEGIARTI000000000601": boucle}, legifrance.origine_codification, boucle)
        self.assertEqual(r["textes"], [])
        self.assertEqual(r["chemin"], ["Boucle"])      # une remontée sans résultat n'allonge pas le chemin

    def test_textes_produisant(self):
        modifiee = {"lienModifications": [lien("MODIFIE", "cible", "JORFTEXT000000000015", "2016-02-11")]}
        self.assertEqual(self.appeler({}, legifrance.textes_produisant, modifiee)[1], None)
        sans_origine = self.article_codifie()
        liens, codification = self.appeler({}, legifrance.textes_produisant, sans_origine)
        self.assertEqual([l["textCid"] for l in liens], ["JORFTEXT000000000011", "JORFTEXT000000000012"])
        self.assertIsNone(codification)
        ancien = {"id": "LEGIARTI000000000301", "lienModifications": []}
        avec_origine = self.article_codifie(
            concordance("CONCORDE", "cible", "LEGIARTI000000000301", "Loi fictive 83 - art. 1 (Ab)",
                        cid="JORFTEXT000000000042"))
        liens, codification = self.appeler({"LEGIARTI000000000301": ancien},
                                           legifrance.textes_produisant, avec_origine)
        self.assertEqual([l["textCid"] for l in liens], ["JORFTEXT000000000042"])
        self.assertEqual(codification["issu_de"], ["Loi fictive 83 - art. 1 (Ab)"])
        self.assertEqual(len(codification["codifie_par"]), 2)


class HistoriqueTextes(unittest.TestCase):
    """historique_article : chaque version porte `modifs`, ses textes, et `modif` quand il est seul.
    PISTE simulé ; identifiants fictifs."""

    def historique(self, liens):
        version = {"id": "LEGIARTI000000000004", "version": "1.0", "dateDebut": None, "dateFin": None}
        normal = post_en_panne("/aucun", num_rendu="L181-18", versions=[version])

        def _post(chemin, charge):
            reponse = normal(chemin, charge)
            if chemin == "/consult/getArticle" and charge["id"] == version["id"]:
                reponse["article"]["lienModifications"] = liens
            return reponse
        with mock.patch.object(legifrance, "_CODES_MAP", {"code de l'environnement": "Code de l'environnement"}), \
             mock.patch.object(legifrance, "_post", _post):
            return legifrance.historique_article("Code de l'environnement", "L. 181-18", "2024-03-15")

    def test_un_texte(self):
        v = self.historique([lien("MODIFIE", "cible", "JORFTEXT000000000015", "2016-02-11"),
                             TextesDeVersion.CODIF_1])["versions"][0]
        self.assertEqual(len(v["modifs"]), 1)
        self.assertEqual(v["modif"], v["modifs"][0])
        self.assertEqual(v["modif"]["lien"], legifrance._lien_texte("JORFTEXT000000000015"))

    def test_plusieurs_textes_sans_hierarchie(self):
        v = self.historique([lien("MODIFIE", "cible", "JORFTEXT000000000017", "2016-08-09"),
                             lien("MODIFIE", "cible", "JORFTEXT000000000016", "2016-08-05")])["versions"][0]
        self.assertEqual([m["date"] for m in v["modifs"]], ["2016-08-05", "2016-08-09"])
        self.assertIsNone(v["modif"])

    def test_aucun_texte(self):
        v = self.historique([])["versions"][0]
        self.assertEqual(v["modifs"], [])
        self.assertIsNone(v["modif"])


class Structure(unittest.TestCase):
    """La démonstration (`if __name__ == "__main__":`) est la dernière instruction du fichier :
    une fonction définie après elle n'existerait pas encore quand elle s'exécute."""

    def test_demonstration_en_fin_de_fichier(self):
        with open(legifrance.__file__, encoding="utf-8") as f:
            derniere = ast.parse(f.read()).body[-1]
        self.assertIsInstance(derniere, ast.If)
        self.assertIn("__main__", ast.unparse(derniere.test))


if __name__ == "__main__":
    unittest.main()
