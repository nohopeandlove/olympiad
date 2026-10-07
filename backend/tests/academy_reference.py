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

SCHOOL_SOLUTIONS = {
1: SOLUTIONS[1],
2: 'n=int(input())\nprint(max(map(int,input().split())))\n',
3: "s=input()\nprint('YES' if s==s[::-1] else 'NO')\n",
4: 'n=int(input())\nprint(sum(x>0 for x in map(int,input().split())))\n',
5: 'n,k=map(int,input().split())\na=list(map(int,input().split()))\nprint(sum(a[i]+a[j]==k for i in range(n) for j in range(i+1,n)))\n',
6: 'n,s,t=map(int,input().split())\na=list(map(int,input().split()))\nprint(-1 if any(a[min(s,t)-1:max(s,t)]) else abs(s-t))\n',
7: 'n=int(input())\nprint((n+1)//2)\n',
8: 'n,p=map(int,input().split())\nprint(min(n-1,1+n-p))\n',
9: "n=int(input())\nprint(sum(input()=='ERROR' for _ in range(n)))\n",
10: 'n=int(input())\na=list(map(int,input().split()))\nbest=length=0\nfor x in a:\n length=length+1 if x==1 else 0\n best=max(best,length)\nprint(best)\n',
11: 'n=int(input())\nprint(*sorted(map(int,input().split())))\n',
12: "s=input()\nbalance=0\nvalid=True\nfor c in s:\n balance+=1 if c=='(' else -1\n if balance<0:valid=False\nprint('YES' if valid and balance==0 else 'NO')\n",
13: '''h,w=map(int,input().split())
dp=[float('inf')]*w
dp[0]=0
for r in range(h):
 a=list(map(int,input().split()))
 for c in range(w):
  dp[c]=a[c]+min(dp[c],dp[c-1] if c else float('inf'))
print(dp[-1])
''',
14: 'print(len(set(input())))\n',
}
SPO_SOLUTIONS = {**SOLUTIONS,
1: 'n=int(input())\nwhile n>=10:n=sum(map(int,str(n)))\nprint(n)\n',
9: '''n,q=map(int,input().split())
p=[0]
for x in map(int,input().split()):p.append(p[-1]+x)
for _ in range(q):
 l,r=map(int,input().split())
 print(p[r]-p[l-1])
''',
10: '''n,k=map(int,input().split())
a=list(map(int,input().split()))
left=total=0
best=n+1
for right,x in enumerate(a):
 total+=x
 while total>=k:
  best=min(best,right-left+1)
  total-=a[left]
  left+=1
print(best if best<=n else 0)
''',
11: '''import heapq
p,n=map(int,input().split())
queue=[(0,i) for i in range(1,p+1)]
heapq.heapify(queue)
for t in map(int,input().split()):
 start,robot=heapq.heappop(queue)
 print(robot,start)
 heapq.heappush(queue,(start+t,robot))
''',
12: '''s=input()
stack=[]
valid=True
for c in s:
 if c in '([{':stack.append(c)
 elif not stack or stack.pop()!={')':'(',']':'[','}':'{'}[c]:
  valid=False
  break
print('YES' if valid and not stack else 'NO')
''',
13: '''h,w=map(int,input().split())
dp=[float('inf')]*w
dp[0]=0
for r in range(h):
 a=list(map(int,input().split()))
 for c in range(w):
  dp[c]=float('inf') if a[c]<0 else a[c]+min(dp[c],dp[c-1] if c else float('inf'))
print(-1 if dp[-1]==float('inf') else dp[-1])
''',
14: '''s=input()
last={}
left=best=0
for right,c in enumerate(s):
 left=max(left,last.get(c,-1)+1)
 last[c]=right
 best=max(best,right-left+1)
print(best)
''',
}
CATEGORY_SOLUTIONS = {'SCHOOL': SCHOOL_SOLUTIONS, 'SPO': SPO_SOLUTIONS}
