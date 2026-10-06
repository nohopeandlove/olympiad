"""Private reference programs used only to validate authored cases and the judge."""
SOLUTIONS = {
1: '''n = int(input())
s = 0
while n:
    s += n % 10
    n //= 10
print(s)
''',
2: '''n = int(input())
a = sorted(set(map(int, input().split())), reverse=True)
print(a[1] if len(a) > 1 else 'NO')
''',
3: '''s = input()
left, right = 0, len(s) - 1
while left < right and s[left] == s[right]:
    left += 1
    right -= 1
first = s[left + 1:right + 1]
second = s[left:right]
print('YES' if first == first[::-1] or second == second[::-1] else 'NO')
''',
4: '''n = int(input())
a = list(map(int, input().split()))
best = length = 1
for i in range(1, n):
    length = length + 1 if a[i] > a[i-1] else 1
    best = max(best, length)
print(best)
''',
5: '''from collections import defaultdict
n, k = map(int, input().split())
seen = defaultdict(int)
answer = 0
for number in map(int, input().split()):
    answer += seen[k-number]
    seen[number] += 1
print(answer)
''',
6: '''from collections import deque
h, w = map(int, input().split())
grid = [input() for _ in range(h)]
for r in range(h):
    for c in range(w):
        if grid[r][c] == 'S': start = (r,c)
queue = deque([start])
distance = {start: 0}
answer = -1
while queue:
    r, c = queue.popleft()
    if grid[r][c] == 'T':
        answer = distance[r,c]
        break
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        nr, nc = r+dr, c+dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != '#' and (nr,nc) not in distance:
            distance[nr,nc] = distance[r,c]+1
            queue.append((nr,nc))
print(answer)
''',
7: '''n = int(input())
counts = [0]
for total in range(1, n+1):
    counts.append(min(counts[total-capacity]+1 for capacity in (1,3,4) if capacity <= total))
print(counts[n])
''',
8: '''from collections import deque
n = int(input())
teleports = [int(x)-1 for x in input().split()]
distance = [-1]*n
distance[0] = 0
queue = deque([0])
while queue:
    node = queue.popleft()
    if node == n-1: break
    for target in (node-1, node+1, teleports[node]):
        if 0 <= target < n and distance[target] == -1:
            distance[target] = distance[node]+1
            queue.append(target)
print(distance[-1])
''',
}
