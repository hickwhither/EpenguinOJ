Trạng thái: chưa làm hehe
# Hệ thống solo code CF
Codeforces giới hạn 1 request mỗi 2 giây.

## Xác nhận người dùng
Người dùng đặt first name theo hash jwt, server đọc và xác nhận

GET https://codeforces.com/api/user.info?handles=hickwhither&checkHistoricHandles=false
```json
{
  "status": "OK",
  "result": [
    {
      "lastName": "dep trai",
      "lastOnlineTimeSeconds": 1784807217,
      "rating": 1291,
      "friendOfCount": 14,
      "titlePhoto": "https://userpic.codeforces.org/2353660/title/11dc6e8022413b12.jpg",
      "handle": "HickWhither", // Sửa handle theo cái này
      "avatar": "https://userpic.codeforces.org/2353660/avatar/6cb7dc5ccc223c7d.jpg",
      "firstName": "Toi", // Kiemr tra cai nay
      "contribution": -1,
      "organization": "",
      "rank": "pupil",
      "maxRating": 1459,
      "registrationTimeSeconds": 1638786608,
      "maxRank": "specialist"
    }
  ]
}
```

## Danh sách bài CF
Chỉ cập nhật mỗi ngày hoặc mỗi tuần vì cái này khá nặng (Thật ra cũng không nặng lắm)

GET https://codeforces.com/api/problemset.problems
```json
{
  "status": "OK",
  "result": {
    "problems": [
      {
        "contestId": 2245, // IMPORTANT
        "index": "D1", // IMPORTANT
        "name": "Construct an Array (Easy Version)",
        "type": "PROGRAMMING",
        "points": 1500.0, // Rating
        "tags": [ // Tags
          "dfs and similar",
          "implementation",
          "sortings"
        ]
      },...
    ],
    "problemStatistics": [
      {
        "contestId": 2245,
        "index": "D2",
        "solvedCount": 1634
      },...
    ]
  }
}
```


## Danh sách AC của người dùng
Không năng như danh sách trên vì ai đời lại nộp nhiều bài đến thế =))

Nên gửi request mỗi lần solo

GET https://codeforces.com/api/user.status?handle=hickwhither
```json
{
  "status": "OK",
  "result": [
    {
      "id": 377460874,
      "contestId": 1,
      "creationTimeSeconds": 1780726301,
      "relativeTimeSeconds": 2147483647,
      "problem": {
        "contestId": 1, // IMPORTANT
        "index": "A", // IMPORTANT
        "name": "Theatre Square",
        "type": "PROGRAMMING",
        "rating": 1000,
        "tags": [
          "math"
        ]
      },
      "author": {
        "contestId": 1,
        "participantId": 238396654,
        "members": [
          {
            "handle": "HickWhither"
          }
        ],
        "participantType": "PRACTICE",
        "ghost": false,
        "startTimeSeconds": 1266580800
      },
      "programmingLanguage": "C++17 (GCC 7-32)",
      "verdict": "COMPILATION_ERROR", // IMPORTANT
      "testset": "TESTS",
      "passedTestCount": 0,
      "timeConsumedMillis": 0,
      "memoryConsumedBytes": 0
    },...
  ]
}
```
