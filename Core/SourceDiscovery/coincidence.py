#!/usr/bin/env python
# -*- coding:utf-8 -*-


class DomainComparator:

    def __init__(self):
        self.data1 = [['fortinet.com', {'pypi': 128, 'npm': 6}], ['stackoverflow.com', {'pypi': 72, 'npm': 115}], ['reversinglabs.com', {'pypi': 77, 'npm': 7}], ['thehackernews.com', {'pypi': 142, 'npm': 64}], ['github.io', {'pypi': 393, 'npm': 1798}], ['python.org', {'pypi': 59, 'npm': 2}], ['quora.com', {'pypi': 9, 'npm': 43}], ['github.com', {'pypi': 1118, 'npm': 584}], ['readthedocs.io', {'pypi': 77, 'npm': 42}], ['archive.org', {'pypi': 36, 'npm': 59}], ['academia.edu', {'pypi': 27, 'npm': 30}], ['csdn.net', {'pypi': 80, 'npm': 44}], ['readthedocs.org', {'pypi': 50, 'npm': 12}], ['rssing.com', {'pypi': 82, 'npm': 38}], ['dokumen.pub', {'pypi': 21, 'npm': 58}], ['githubusercontent.com', {'pypi': 21, 'npm': 52}], ['wordpress.com', {'pypi': 28, 'npm': 32}], ['phylum.io', {'pypi': 1177, 'npm': 826}], ['cyble.com', {'pypi': 80}], ['reddit.com', {'pypi': 494, 'npm': 79}], ['codeberg.org', {'pypi': 158}], ['securityaffairs.com', {'pypi': 55, 'npm': 7}], ['bleepingcomputer.com', {'pypi': 121, 'npm': 67}], ['arxiv.org', {'pypi': 64, 'npm': 58}], ['researchgate.net', {'pypi': 50, 'npm': 18}], ['cybersecuritynews.com', {'pypi': 50, 'npm': 12}], ['iototsecnews.jp', {'pypi': 104, 'npm': 97}], ['medium.com', {'pypi': 84, 'npm': 103}], ['scribd.com', {'pypi': 26, 'npm': 73}], ['rhisac.org', {'pypi': 280}], ['checkmarx.com', {'pypi': 52, 'npm': 26}], ['trendmicro.com', {'pypi': 47, 'npm': 10}], ['sonatype.com', {'pypi': 284, 'npm': 124}], ['qianxin.com', {'pypi': 46, 'npm': 6}], ['cyware.com', {'pypi': 55, 'npm': 12}], ['arstechnica.com', {'pypi': 51, 'npm': 19}], ['securityweek.com', {'pypi': 58, 'npm': 3}], ['jfrog.com', {'pypi': 61, 'npm': 262}], ['thesecmaster.com', {'pypi': 7, 'npm': 221}], ['mitre.org', {'pypi': 40, 'npm': 71}], ['cvedetails.com', {'pypi': 4, 'npm': 59}], ['ycombinator.com', {'pypi': 41, 'npm': 66}], ['socket.dev', {'pypi': 29, 'npm': 141}], ['linknovate.com', {'pypi': 6, 'npm': 114}], ['snyk.io', {'pypi': 43, 'npm': 245}], ['linkedin.com', {'pypi': 98, 'npm': 85}], ['stackexchange.com', {'pypi': 48, 'npm': 13}], ['socradar.io', {'pypi': 41, 'npm': 32}], ['debian.org', {'pypi': 24, 'npm': 40}], ['datadoghq.com', {'pypi': 99, 'npm': 15}], ['unitn.it', {'pypi': 58, 'npm': 14}], ['microsoft.com', {'pypi': 4, 'npm': 101}], ['dev.to', {'pypi': 8, 'npm': 45}], ['scaprepo.com', {'pypi': 7, 'npm': 45}], ['hybrid-analysis.com', {'pypi': 21, 'npm': 122}], ['deps.dev', {'pypi': 6, 'npm': 478}], ['appsloveworld.com', {'pypi': 1, 'npm': 57}], ['glideapps.com', {'npm': 107}], ['genetec.com', {'npm': 179}], ['netapp.com', {'npm': 90}], ['irbbarcelona.org', {'npm': 90}], ['grammarly.com', {'npm': 160}], ['deloitte.com', {'npm': 172}], ['parity.io', {'npm': 112}], ['unpkg.com', {'npm': 64}]]
        self.data2 = [['reversinglabs.com', {'pypi': 4}], ['npmjs.com', {'npm': 635}], ['fortinet.com', {'pypi': 58}], ['gitlab.com', {'pypi': 1}], ['bleepingcomputer.com', {'pypi': 20}], ['securityboulevard.com', {'pypi': 1}], ['twitter.com', {'pypi': 3}], ['thehackernews.com', {'npm': 1}], ['runkit.com', {'npm': 1}], ['medium.com', {'pypi': 1769, 'npm': 31}], ['pytorch.org', {'pypi': 1}], ['phylum.io', {'pypi': 78, 'npm': 157}], ['github.com', {'pypi': 349, 'npm': 63}], ['jfrog.com', {'pypi': 5}], ['checkmarx.com', {'pypi': 13}], ['sonatype.com', {'pypi': 182}], ['apiiro.com', {'pypi': 1}], ['socket.dev', {'pypi': 1}]]

    def get_domains(self, data):
        return set([item[0] for item in data])

    def compare_domains(self):
        domains_data1 = self.get_domains(self.data1)
        domains_data2 = self.get_domains(self.data2)
        common_domains = domains_data1.intersection(domains_data2)
        unique_in_data1 = domains_data1 - domains_data2
        unique_in_data2 = domains_data2 - domains_data1
        return {
            "common_domains": common_domains,
            "unique_in_data1": unique_in_data1,
            "unique_in_data2": unique_in_data2,
            "count_common": len(common_domains),
            "count_unique_in_data1": len(unique_in_data1),
            "count_unique_in_data2": len(unique_in_data2)
        }


if __name__ == '__main__':
    comparator = DomainComparator()
    result = comparator.compare_domains()
    print("Common Domains:", result["common_domains"], "Count:", result["count_common"])
    print("Unique in Data1:", result["unique_in_data1"], "Count:", result["count_unique_in_data1"])
    print("Unique in Data2:", result["unique_in_data2"], "Count:", result["count_unique_in_data2"])
