# Household differential pairs experiments

## Lab session 1

Materials and lab assistant:

![20260227_030917](pictures/20260227_030917.jpg)

Reference: the differential pair without its shield (but still with a ground connexion) displaying the picture:

![20260227_031754](pictures/20260227_031754.jpg)

First shot to see the effect of a ground on impedance: when the lines of the differential pair are pulled away, the link does not work anymore, except when a ground plane is present. Note that no particular attempt was here made to check the effect of disconnecting this ground:

![20260227_032530](pictures/20260227_032530.jpg)

![20260227_032406](pictures/20260227_032406.jpg)

Next, attempt to cross a slot. The link works, proving that the differential pair needs the ground to work for impedance reasons, but can still withstand a slot. This slot is not perfect, limiting the strength of the demonstration, but gives confidence to continue the work:

![20260227_033517](pictures/20260227_033517.jpg)

![20260227_033529](pictures/20260227_033529.jpg)

The reason why differential pairs behave in this way is that, on the slot, the return current on each line connects with the return current of the other line, like in the picture below:

![diff-pair-ground-current-slot](diff-pair-ground-current-slot.png)

To test this, a double slot was tested. Even if the results of this test match what is expected, the slots made with household resources were not very clean:

![20260227_034638](pictures/20260227_034638.jpg)

![20260227_034645](pictures/20260227_034645.jpg)

After this test, I took just in case some measurements, but for the following of the study I will probably make some calculations of EM simulations:

![20260227_034804](pictures/20260227_034804.jpg)

![20260227_034809](pictures/20260227_034809.jpg)

![20260227_034814](pictures/20260227_034814.jpg)

Total time spent between first and last pictures: 48 minutes.

## Discussions about the frequencies

The screen used for the tests had a 1920×1080 resolution with a refresh frequency of 60 Hz. Assuming most common parameters for control data and sound channels, according to [https://en.wikipedia.org/wiki/HDMI#Resolution_and_refresh_frequency_limits](https://en.wikipedia.org/wiki/HDMI#Resolution_and_refresh_frequency_limits), a total bitrate of 3.20 Gbit/s is needed, that is 1.07 Gbit/s on each of the 3 data differential pairs, equivalent to a Nyquist frequency of 533 MHz.

Definitely not a very high speed differential pair. For instance, PCI Express uses 2.5 Gbit/s differential pairs since 2003 [https://en.wikipedia.org/wiki/PCI_Express#Comparison_table](https://en.wikipedia.org/wiki/PCI_Express#Comparison_table). Still an interesting experiment, particularly for electronics students.
