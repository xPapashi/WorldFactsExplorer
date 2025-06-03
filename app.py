import requests
import xml.etree.ElementTree as ET
import xmltodict
from flask import Flask, jsonify, render_template, send_file, request, abort, Response
from io import BytesIO

app = Flask(__name__)

RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
XML_CACHE = None

def fetch_and_convert_to_xml():
    resp = requests.get(RESTCOUNTRIES_URL)
    resp.raise_for_status()
    countries = resp.json()
    root = ET.Element("world")
    for c in countries:
        name = c.get("name", {}).get("common", "Unknown")
        capital = (c.get("capital") or ["Unknown"])[0]
        population = c.get("population", 0)
        languages = c.get("languages", {})
        language = ", ".join(languages.values()) if languages else "Unknown"
        currencies = c.get("currencies", {})
        currency = ", ".join([v.get("name", "") for v in currencies.values()]) if currencies else "Unknown"
        timezones = c.get("timezones", [])
        timezone = ", ".join(timezones) if timezones else "Unknown"

        country = ET.SubElement(root, "country", name=name)
        ET.SubElement(country, "capital").text = capital
        ET.SubElement(country, "population").text = str(population)
        ET.SubElement(country, "language").text = language
        ET.SubElement(country, "currency").text = currency
        ET.SubElement(country, "timezone").text = timezone
    return ET.tostring(root, encoding="utf-8")

def get_xml_data():
    global XML_CACHE
    if XML_CACHE is None:
        XML_CACHE = fetch_and_convert_to_xml()
    return XML_CACHE

def parse_xml_to_dict(xml_bytes):
    return xmltodict.parse(xml_bytes)["world"]["country"]

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/countries")
def countries():
    xml_bytes = get_xml_data()
    countries = parse_xml_to_dict(xml_bytes)
    # Filtering
    language = request.args.get("language")
    if language:
        countries = [c for c in countries if language.lower() in (c.get("language", "") or "").lower()]
    return jsonify(countries)

@app.route("/countries/<name>")
def country_by_name(name):
    xml_bytes = get_xml_data()
    countries = parse_xml_to_dict(xml_bytes)
    for c in countries:
        if c["@name"].lower() == name.lower():
            return jsonify(c)
    abort(404, description="Country not found")

@app.route("/countries.xml")
def countries_xml():
    xml_bytes = get_xml_data()
    return Response(xml_bytes, mimetype="application/xml")

if __name__ == "__main__":
    app.run(debug=True)