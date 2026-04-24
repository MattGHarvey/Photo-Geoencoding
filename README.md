# Photo Geoencoding

A custom KML file for geocoding custom places in Adobe Lightroom using Jeffrey Friedl's **Geoencoding Support** plugin.

## Plugin

**Jeffrey's "Geoencoding Support" Plugin for Lightroom**
https://regex.info/blog/lightroom-goodies/gps

This plugin allows Lightroom to reverse-geocode GPS coordinates in photos — looking up place names (city, region, country, etc.) from latitude/longitude data embedded in your photos.

## Custom KML File

`Photo Geocoding.kml` defines custom named locations that the plugin uses when reverse-geocoding photo coordinates. This is useful for:

- Named locations not covered (or incorrectly named) by the plugin's default data sources
- Private properties, rural areas, or local landmarks
- Consistent, custom place names across a photo library

## Usage

1. Install Jeffrey's Geoencoding Support Plugin in Lightroom.
2. In the plugin settings, point it to this KML file as a custom location source.
3. When geocoding photos, the plugin will match GPS coordinates against the regions defined in this file and apply the custom place names.

## Author

Matt Harvey — [75CentralPhotography.com](https://75CentralPhotography.com) · [RobotSprocket.com](https://robotsprocket.com)

## Contributing

Pull requests are welcome! If you have custom locations to add or corrections to existing ones, feel free to open a PR.

## License

This project is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license. You are free to share and adapt the material for any purpose, including commercially, as long as you give appropriate credit.

## Resources

- Plugin homepage: https://regex.info/blog/lightroom-goodies/gps
- KML format reference: https://developers.google.com/kml/documentation
