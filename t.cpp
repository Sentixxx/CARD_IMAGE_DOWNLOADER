#include <bits/stdc++.h>

int main() {
    std::cin.tie(0);
    std::ios::sync_with_stdio(false);

    int n;
    std::cin >> n;
    std::string s;
    std::cin >> s;

    int m;
    std::cin >> m;
    std::vector<std::string> t(m);

    for(int i = 0;i < m;i++)
        std::cin >> t[i];

    std::vector<int> p(m,0);

    int ans = 0;
    for(int i = 0;i < n;i++) {
        for(int j = 0;j < m;j++) {
            if(p[j] < t[j].size() && t[j][p[j]] == s[i]) {
                p[j]++;
                if(p[j] == t[j].size()) {
                    ans++;
                }
            }
        }
    }

    std::cout << ans << "\n";
    


}