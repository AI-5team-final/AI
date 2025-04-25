def test_sorting_by_total_score():
    # 모의 데이터
    results = [
        {"object_id": "1", "total_score": 80, "other_field": "A"},
        {"object_id": "2", "total_score": 95, "other_field": "B"},
        {"object_id": "3", "total_score": 70, "other_field": "C"},
        {"object_id": "4", "total_score": 85, "other_field": "D"},
    ]

    # total_score에 따라 내림차순으로 정렬
    sorted_results = sorted(results, key=lambda x: x["total_score"], reverse=True)

    # total_score를 제외하고 final_results 생성
    final_results = [
        {k: v for k, v in item.items() if k != "total_score"}
        for item in sorted_results
    ]

    # 예상되는 정렬된 결과
    expected_results = [
        {"object_id": "2", "other_field": "B"},
        {"object_id": "4", "other_field": "D"},
        {"object_id": "1", "other_field": "A"},
        {"object_id": "3", "other_field": "C"},
    ]

    # 정렬된 결과가 예상과 일치하는지 확인
    assert final_results == expected_results, f"Expected {expected_results}, but got {final_results}"

# 테스트 실행
test_sorting_by_total_score()