# Label association in xTRam1/safe-guard-prompt-injection

10296 rows, attack base rate 30.6%. Whole-word, case-insensitive.

| word | kind | rows containing it | share attack | lift | model median score in slot test |
|---|---|---:|---:|---:|---:|
| `charged` | financial | 15 | 7% | 0.22x | 0.000 |
| `debited` | financial | 0 | - | - | 0.001 |
| `refunded` | financial | 0 | - | - | 0.000 |
| `invoiced` | financial | 0 | - | - | 0.000 |
| `reimbursed` | financial | 2 | 0% | 0.00x | 0.000 |
| `paid` | financial | 38 | 8% | 0.26x | 0.000 |
| `billed` | financial | 3 | 0% | 0.00x | 0.000 |
| `credited` | financial | 4 | 0% | 0.00x | 0.981 |
| `authorized` | financial | 15 | 87% | 2.84x | 1.000 |
| `preauthorized` | financial | 0 | - | - | 1.000 |
| `approved` | financial | 7 | 29% | 0.94x | 0.000 |
| `declined` | financial | 6 | 0% | 0.00x | 0.000 |
| `encrypted` | security | 5 | 60% | 1.96x | 1.000 |
| `decrypted` | security | 1 | 0% | 0.00x | 1.000 |
| `hashed` | security | 0 | - | - | 0.998 |
| `signed` | security | 13 | 0% | 0.00x | 0.002 |
| `verified` | security | 97 | 60% | 1.96x | 0.994 |
| `authenticated` | security | 0 | - | - | 0.007 |
| `locked` | security | 11 | 36% | 1.19x | 0.000 |
| `unlocked` | security | 4 | 50% | 1.64x | 1.000 |
| `revoked` | security | 3 | 33% | 1.09x | 0.000 |
| `reset` | security | 20 | 95% | 3.11x | 0.027 |
| `updated` | account | 14 | 21% | 0.70x | 0.000 |
| `confirmed` | account | 16 | 12% | 0.41x | 0.000 |
| `issued` | account | 9 | 11% | 0.36x | 0.000 |
| `renewed` | account | 2 | 0% | 0.00x | 0.000 |
| `cancelled` | account | 5 | 0% | 0.00x | 0.000 |
| `activated` | account | 7 | 100% | 3.27x | 0.970 |
| `deactivated` | account | 1 | 100% | 3.27x | 0.980 |
| `provisioned` | account | 0 | - | - | 0.000 |
| `processed` | account | 6 | 50% | 1.64x | 0.000 |
| `scheduled` | account | 10 | 0% | 0.00x | 0.000 |
| `mown` | everyday | 0 | - | - | 0.000 |
| `baked` | everyday | 4 | 0% | 0.00x | 0.000 |
| `painted` | everyday | 10 | 0% | 0.00x | 0.000 |
| `cleaned` | everyday | 2 | 0% | 0.00x | 0.000 |
| `watered` | everyday | 1 | 0% | 0.00x | 0.000 |
| `repaired` | everyday | 1 | 0% | 0.00x | 0.000 |
| `delivered` | everyday | 12 | 0% | 0.00x | 0.000 |
| `washed` | everyday | 3 | 0% | 0.00x | 0.000 |
| `stirred` | everyday | 0 | - | - | 0.000 |
| `folded` | everyday | 1 | 0% | 0.00x | 0.000 |
| `photosynthesized` | rare | 0 | - | - | 0.000 |
| `lyophilized` | rare | 0 | - | - | 0.000 |
| `defenestrated` | rare | 0 | - | - | 0.000 |
| `pasteurized` | rare | 0 | - | - | 0.000 |
| `recrystallized` | rare | 0 | - | - | 0.000 |
| `galvanized` | rare | 1 | 0% | 0.00x | 0.000 |
| `vulcanized` | rare | 0 | - | - | 0.000 |
| `desalinated` | rare | 0 | - | - | 0.000 |
| `annealed` | rare | 0 | - | - | 0.000 |
| `tessellated` | rare | 0 | - | - | 0.000 |

Spearman correlation between lift and the model's MEDIAN score over the five frames, words with at least 5 rows: rho = 0.72 (n = 19 words), permutation p = 0.0011 (two-sided, 10,000 permutations), bootstrap 95% interval [0.38, 0.90]
