# Additional Bus Specifications
`additional_bus_specs.json` contains additional information which the BusTimes API does not provide by default, including the average capacity, height and length (in metres) for that category of bus (e.g. ALX400, Optare Solo SR).

Only the buses present in **Brylaine Travel's** fleet (code *BRYL*) as of **February 2026** are in the dataset, as multi-operator evaluation was outside the scope of the research project. However, any additions via pull requests would be gladly accepted.

## Format
- **name**: the type of bus, according to BusTime's API.
- **capacity**: the mean capacity of the bus
- **length**: the average length of the bus
- **height**: the height of the bus

## Sources
- [Optare Solo SR](https://www.optare.com/wp-content/uploads/2020/11/SoloSpecSheetOct2018AW8pp.pdf)
- [Optare Solo](https://web.archive.org/web/20040621220513/http://www.optare.com/Images/Products/solo.pdf)
- [Optare Tempo](https://web.archive.org/web/20060327102713/http://www.optare.com/Images/Products/tempo.pdf)
- [Optare Versa](https://web.archive.org/web/20131018042635/http://www.optare.com/images/brochures/versa%20spec.pdf)
- Due to insufficient information regarding Gemini Specifications, the height of the [Gemini 3](https://web.archive.org/web/20190924184456/http://www.wrightsgroup.com/datasheets/A3%20B5TL%20Gemini%203%20UpdateGR.pdf) was used for all Eclipse Gemini buses, additional to the specification sheet of the [Volvo B7TL Write Eclipse Gemini](https://web.archive.org/web/20051111044151/http://www.wrightbus.com/bus_produc_dd.htm).
- ALX400s were sourced from their [2005 webpage](https://web.archive.org/web/20050617014622/http://www.alexander-dennis.com/double_deck/alx.htm) and a [listing to buy one](https://web.archive.org/web/20260131214307/https://ukbussales.com/vehicles/2004-dennis-trident-alexander-alx400/).