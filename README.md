# [_**Navi Corpus**_](http://yoavartzi.com/navi)

**Developed and maintained by** [Yoav Artzi](http://yoavartzi.com). Based on data from Chen and Mooney 2011 and MacMahon et al. 2006.

**It's highly recommended to use the data as available in the [Navi repository](http://yoavartzi.com/navi).**

## Documentations

The corpus includes two version:
1. The original segmented corpus as used by Chen and Mooney in 2011. This data is split into 3 folds for cross-validation over the 3 different maps.
2. The cleaned up Oracle version of the corpus (see Artzi and Zettlemoyer 2013 for details about the cleanup process). This data is divided into two randomly selected sets, one for test and one for training and development. The development set is divided into random splits for cross-validation during development. 

The directory `tacl-data` includes the processed version of the two corpora above in the format used in Artzi and Zettlemoyer 2013. The original SAIL corpus is in the `sail` directory. The directory `navi` includes the development of the Oracle corpus. Finally, the directory `pysrc` includes various utilities.

## Attribution

When using this corpus, please acknowledge it by citing:

Artzi, Yoav and Zettlemoyer, Luke. "Weakly Supervised Learning of Semantic Parsers for Mapping Instructions to Actions." In Transactions of the Association for Computational Linguistics (TACL), 2013.

**Bibtex:**

    @article{artzi-zettlemoyer:2011:TACL,
        title={Weakly Supervised Learning of Semantic Parsers for Mapping Instructions to Actions},
        author={Artzi, Yoav and Zettlemoyer, Luke},
        journal={Transactions of the Association for Computational Linguistics},
        volume={1},
        number={1},
        pages={49--62},
        year={2013},
        publisher={Association for Computational Linguistic}
    }

**Also, please cite the original creators of the corpus:**

    @InProceedings{macmahon:aaai06,
        title = "Walk the Talk: Connecting Language, Knowledge, and Action in Route Instructions",
        author = "Matt MacMahon and Brian Stankiewicz and Benjamin Kuipers",
        booktitle = "Proceedings of the 21st National Conference on Artificial Intelligence (AAAI-2006)",
        address = "Boston, MA, USA",
        month = "July",
        year = 2006
    } 

    @InProceedings{chen:aaai11,
        title = "Learning to Interpret Natural Language Navigation Instructions fro mObservations",
        author = "David L. Chen and Raymond J. Mooney",
        booktitle = "Proceedings of the 25th AAAI Conference on Artificial Intelligence (AAAI-2011)",
        address = "San Francisco, CA, USA",
        month = "August",
        year = 2011
    } 


## License

Navi Corpus

Copyright (C) 2013 Yoav Artzi

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 51
Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
